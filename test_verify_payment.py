import importlib.util, os
spec = importlib.util.spec_from_file_location("vp", os.path.join(os.path.dirname(__file__), "verify_payment.py"))
vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)
vp.WALLET = W = "9aQdvZXv1Rq2wx9QrekAGivLVdGRkSiSBNz8Uefi3PUk"


def tx(micro, owner=W, mint=vp.USDC, err=None):
    b = lambda a: {"owner": owner, "mint": mint, "uiTokenAmount": {"amount": str(a)}}
    return {"slot": 1, "blockTime": 1792500000, "meta": {"err": err, "preTokenBalances": [b(0)], "postTokenBalances": [b(micro)]},
            "transaction": {"message": {"accountKeys": [{"pubkey": "Payer111"}]}}}


def test_verdicts():
    assert vp.verdict("s", tx(29_004_321), "29.004321")["ok"]
    assert vp.verdict("s", tx(29_000_000), "29.004321")["reason"] == "underpaid"
    assert vp.verdict("s", tx(29_000_000, mint="Fake"), None)["reason"] == "no_usdc_to_wallet"
    assert vp.verdict("s", tx(1, err={"x": 1}))["reason"] == "transaction_failed"
    assert vp.verdict("s", None)["reason"] == "not_found_or_not_finalized"
    v = vp.verdict("s", tx(19_000_000))
    assert v["usdc_received"] == "19" and v["payer"] == "Payer111" and v["block_time"].endswith("+00:00")
