#!/usr/bin/env python3
"""Independent on-chain check of a USDC payment to the seller wallet, for the ledger.

  python verify_payment.py --sig <signature> [--amount 29.004321] [--save ../../evidence]
  python verify_payment.py --reference <solana-pay-reference> [--amount ...]
  python verify_payment.py --recent 20          # list recent USDC receipts to the wallet

Uses only public JSON-RPC and the finalized commitment. Never needs a private key.
"""
import argparse, json, os, sys, time, urllib.request
from datetime import datetime, timezone, timedelta
from decimal import Decimal

RPC = os.environ.get("RPC_URL", "https://api.mainnet-beta.solana.com")
WALLET = os.environ.get("RECIPIENT", "")
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
PKT = timezone(timedelta(hours=int(os.environ.get("TZ_OFFSET_HOURS", "0"))))  # display offset for block times


def rpc(method, params):
    req = urllib.request.Request(RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                 {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        j = json.load(r)
    if "error" in j:
        raise RuntimeError(j["error"])
    return j["result"]


def get_tx(sig):
    return rpc("getTransaction", [sig, {"encoding": "jsonParsed", "commitment": "finalized", "maxSupportedTransactionVersion": 0}])


def received_micro(tx, owner=None):
    owner = owner or WALLET
    def total(key):
        return sum(int(b["uiTokenAmount"]["amount"]) for b in (tx["meta"].get(key) or [])
                   if b.get("owner") == owner and b.get("mint") == USDC)
    return total("postTokenBalances") - total("preTokenBalances")


def payer(tx):
    keys = tx["transaction"]["message"]["accountKeys"]
    return keys[0]["pubkey"] if isinstance(keys[0], dict) else keys[0]


def verdict(sig, tx, want=None):
    if tx is None:
        return {"signature": sig, "ok": False, "reason": "not_found_or_not_finalized"}
    if tx["meta"]["err"]:
        return {"signature": sig, "ok": False, "reason": "transaction_failed"}
    got = received_micro(tx)
    out = {"signature": sig, "recipient": WALLET, "payer": payer(tx), "usdc_received": str(Decimal(got) / 10**6),
           "block_time": datetime.fromtimestamp(tx["blockTime"], PKT).isoformat() if tx.get("blockTime") else None,
           "slot": tx["slot"], "explorer": f"https://solscan.io/tx/{sig}"}
    if got <= 0:
        out.update(ok=False, reason="no_usdc_to_wallet")
    elif want is not None and got < int(Decimal(want) * 10**6):
        out.update(ok=False, reason="underpaid")
    else:
        out["ok"] = True
    return out


def main():
    if not WALLET:
        sys.exit("Set RECIPIENT=<your Solana wallet address> (public address only).")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sig"); g.add_argument("--reference"); g.add_argument("--recent", type=int)
    ap.add_argument("--amount", help="expected USDC (minimum)")
    ap.add_argument("--save", help="directory to write a JSON evidence file")
    a = ap.parse_args()

    if a.recent:
        accts = rpc("getTokenAccountsByOwner", [WALLET, {"mint": USDC}, {"encoding": "jsonParsed"}])["value"]
        if not accts:
            print(f"{WALLET} has no USDC token account yet (no USDC ever received)."); return 0
        for acc in accts:
            for s in rpc("getSignaturesForAddress", [acc["pubkey"], {"limit": a.recent, "commitment": "finalized"}]):
                v = verdict(s["signature"], get_tx(s["signature"])); time.sleep(0.2)
                if v.get("ok"):
                    print(f'{v["block_time"]}  +{v["usdc_received"]} USDC  from {v["payer"]}  {v["signature"]}')
        return 0

    sigs = [a.sig] if a.sig else [s["signature"] for s in rpc("getSignaturesForAddress", [a.reference, {"limit": 10}]) if not s["err"]]
    if not sigs:
        print(json.dumps({"reference": a.reference, "ok": False, "reason": "no_transaction_yet"}, indent=2)); return 1
    v = verdict(sigs[0], get_tx(sigs[0]), a.amount)
    if a.reference:
        v["reference"] = a.reference
    print(json.dumps(v, indent=2))
    if a.save and v["ok"]:
        os.makedirs(a.save, exist_ok=True)
        path = os.path.join(a.save, f'payment_{v["signature"][:16]}.json')
        json.dump(v, open(path, "w"), indent=2); print("saved", path)
    return 0 if v["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
