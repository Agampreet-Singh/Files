#!/usr/bin/env python3
"""
ATM Switch Service - Cosmos Bank
Listens for transaction requests from ATM terminals (JSON over TCP socket),
validates the card against the CBS Server database, and approves/declines.

Run as a systemd service (see atm-switch.service) so it survives reboot.
"""

import socket
import json
import logging
import bcrypt
import mysql.connector
from mysql.connector import Error

# ---- Configuration ----
CBS_SERVER_IP = "10.25.0.3"
CBS_DB_USER = "atmswitch"
CBS_DB_PASS = "AtmSwitch2024Secure"
CBS_DB_NAME = "cosmos_bank"

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 5000

logging.basicConfig(
    filename="/var/log/atm-switch.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def get_cbs_connection():
    return mysql.connector.connect(
        host=CBS_SERVER_IP,
        port=3306,
        user=CBS_DB_USER,
        password=CBS_DB_PASS,
        database=CBS_DB_NAME,
        connection_timeout=5
    )


def get_card(cursor, card_number):
    cursor.execute(
        "SELECT balance, pin, status FROM cards WHERE card_number = %s",
        (card_number,)
    )
    return cursor.fetchone()


def check_auth(card, pin):
    """Returns None if OK, or a decline dict if the card/pin is invalid."""
    if not card:
        return {"status": "DECLINED", "reason": "Card not found"}
    if card["status"] != "active":
        return {"status": "DECLINED", "reason": "Card blocked"}
    if not bcrypt.checkpw(str(pin).encode(), str(card["pin"]).encode()):
        return {"status": "DECLINED", "reason": "Incorrect PIN"}
    return None


def process_request(atm_id, action, card_number, pin, amount):
    """Handles verify_pin, withdraw, deposit, balance, and ministatement actions."""
    try:
        conn = get_cbs_connection()
        cursor = conn.cursor(dictionary=True)
        card = get_card(cursor, card_number)
        auth_error = check_auth(card, pin)

        if auth_error:
            result = auth_error

        elif action == "verify_pin":
            result = {"status": "APPROVED", "reason": "PIN verified"}

        elif action == "balance":
            result = {"status": "APPROVED", "reason": "Balance retrieved", "balance": float(card["balance"])}

        elif action == "ministatement":
            cursor.execute(
                "SELECT atm_id, COALESCE(txn_type,'withdrawal') AS txn_type, amount, "
                "balance_after, status, reason, created_at FROM transactions "
                "WHERE card_number = %s ORDER BY created_at DESC LIMIT 5",
                (card_number,)
            )
            rows = cursor.fetchall()
            for r in rows:
                r["amount"] = float(r["amount"])
                r["balance_after"] = float(r["balance_after"]) if r["balance_after"] is not None else None
                r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M")
                r["indicator"] = "Credit" if r["txn_type"] == "deposit" else "Debit"
                r["txn_type"] = r["txn_type"].capitalize()
            result = {"status": "APPROVED", "reason": "Statement retrieved", "transactions": rows}

        elif action == "withdraw":
            if float(amount) > float(card["balance"]):
                result = {"status": "DECLINED", "reason": "Insufficient balance"}
                new_balance = None
            else:
                new_balance = float(card["balance"]) - float(amount)
                cursor.execute(
                    "UPDATE cards SET balance = balance - %s WHERE card_number = %s",
                    (amount, card_number)
                )
                result = {"status": "APPROVED", "reason": "Withdrawal successful", "balance": new_balance}
            cursor.execute(
                "INSERT INTO transactions (card_number, atm_id, txn_type, amount, balance_after, status, reason) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (card_number, atm_id, "withdrawal", amount, new_balance, result["status"].lower(), result["reason"])
            )

        elif action == "deposit":
            new_balance = float(card["balance"]) + float(amount)
            cursor.execute(
                "UPDATE cards SET balance = balance + %s WHERE card_number = %s",
                (amount, card_number)
            )
            result = {"status": "APPROVED", "reason": "Deposit successful", "balance": new_balance}
            cursor.execute(
                "INSERT INTO transactions (card_number, atm_id, txn_type, amount, balance_after, status, reason) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (card_number, atm_id, "deposit", amount, new_balance, result["status"].lower(), result["reason"])
            )

        else:
            result = {"status": "ERROR", "reason": f"Unknown action: {action}"}

        conn.commit()
        cursor.close()
        conn.close()

        logging.info(f"ATM={atm_id} ACTION={action} CARD={card_number} AMOUNT={amount} -> {result}")
        return result

    except Error as e:
        logging.error(f"DB error for ATM={atm_id} ACTION={action} CARD={card_number}: {e}")
        return {"status": "ERROR", "reason": "Switch could not reach CBS Server"}


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(10)
    logging.info(f"ATM Switch listening on {LISTEN_HOST}:{LISTEN_PORT}")
    print(f"[ATM Switch] Listening on {LISTEN_HOST}:{LISTEN_PORT} ...")

    while True:
        client, addr = server.accept()
        try:
            raw = client.recv(1024).decode()
            req = json.loads(raw)
            result = process_request(
                req.get("atm_id", "UNKNOWN"),
                req.get("action", "withdraw"),
                req["card"],
                req["pin"],
                req.get("amount", 0)
            )
            client.send(json.dumps(result).encode())
        except Exception as e:
            logging.error(f"Bad request from {addr}: {e}")
            client.send(json.dumps({"status": "ERROR", "reason": str(e)}).encode())
        finally:
            client.close()


if __name__ == "__main__":
    start_server()
