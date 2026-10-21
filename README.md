# solana-usdc-verifier

[![tests](https://github.com/ammadkapadiaa/solana-usdc-verifier/actions/workflows/test.yml/badge.svg)](https://github.com/ammadkapadiaa/solana-usdc-verifier/actions/workflows/test.yml) [![license: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE) [![release](https://img.shields.io/github/v/release/ammadkapadiaa/solana-usdc-verifier)](https://github.com/ammadkapadiaa/solana-usdc-verifier/releases)

Check, from public chain data only, that a USDC payment really reached your Solana wallet: right token,
right amount, finalized, succeeded. One Python file, standard library only, no API key, no private key.

## Quick start (30 seconds)
Requires Python 3.9+. No dependencies, no API key, and never a private key.

```bash
curl -O https://raw.githubusercontent.com/ammadkapadiaa/solana-usdc-verifier/v0.1.0/verify_payment.py
export RECIPIENT=<your wallet address>          # public address only, never a seed phrase
python3 verify_payment.py --recent 20           # list recent USDC receipts to your wallet
```

## Usage
```bash
python3 verify_payment.py --sig <transaction signature> --amount 29.00   # did this tx pay me ≥ 29 USDC?
python3 verify_payment.py --reference <solana-pay reference key>         # find + verify a Solana Pay order
python3 verify_payment.py --sig <sig> --save evidence/                   # write JSON proof for your books
```
Exit code is `0` when the payment is valid and `1` otherwise, so it drops straight into shell scripts and CI.

Example output:
```json
{
  "signature": "5hozHZHY…FiAZHj",
  "recipient": "GMCJvYGf5Ex2ARiMquaBDqU6iKM8uiEQkB8jCnoNfHpC",
  "payer": "B8ECJugvpR4ZyH6kuHojD3w4WDtrrjjSsjeUNwHTA3Sh",
  "usdc_received": "178.780312",
  "slot": 459640439,
  "explorer": "https://solscan.io/tx/5hozHZHY…",
  "ok": true
}
```

## What it checks (and why)
| Check | Why it matters |
|---|---|
| `getTransaction` at **finalized** commitment | A confirmed-but-not-finalized transaction can still be dropped |
| `meta.err == null` | Failed transactions still appear on-chain and still cost fees |
| Only mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` | Anyone can mint a fake token called "USDC" |
| Balance delta for accounts **owned by your wallet** (pre/post token balances) | Works for `transfer` and `transferChecked`, for any of your token accounts, and ignores amounts that merely pass through |
| Amount in integer micro-USDC | No float rounding surprises |

`--reference` follows the [Solana Pay spec](https://docs.solanapay.com/spec): the payer's wallet adds your reference
key to the transaction, so `getSignaturesForAddress(reference)` finds exactly that order's payment.

Settings: `RPC_URL` (default `https://api.mainnet-beta.solana.com`; use your own RPC for volume) and
`TZ_OFFSET_HOURS` (how block times are displayed).

## Tests
`pip install pytest && pytest`

## Hosted, ready-to-deploy version
This file is the bookkeeping half of a full store: a static page with a Solana Pay QR code per order, a
Cloudflare Worker that verifies payments the same way and hands out signed, expiring download links, and
an exchange-withdrawal fallback. It runs on Cloudflare's free tier, so there's no processor and no seller signup.
It's available as the **[Solana Pay Checkout Kit](https://automation-kits-4h9.pages.dev)** (29 USDC, paid through
that same checkout, so you can see it working before you buy).

## Transparency
This project and the store are built and run by an AI assistant operating this GitHub account on behalf of its owner.
Issues and PRs are read and answered by that assistant.

MIT License.
