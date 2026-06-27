"""Generate (once) a throwaway Cardano PREPROD wallet for on-chain Decision Logging.

  python scripts/cardano_setup.py

Prints the address to fund via the testnet faucet. The signing key is saved to a
gitignored file (preprod test funds only — no real value). After funding + setting
BLOCKFROST_PROJECT_ID, run scripts/cardano_record.py to write a real audit tx.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pycardano import (Address, Network, PaymentSigningKey,  # noqa: E402
                       PaymentVerificationKey)

from config import get_settings  # noqa: E402


def load_or_create():
    skey_path = Path(get_settings().CARDANO_WALLET_SKEY)
    skey_path.parent.mkdir(parents=True, exist_ok=True)
    if skey_path.exists():
        sk = PaymentSigningKey.load(str(skey_path))
    else:
        sk = PaymentSigningKey.generate()
        sk.save(str(skey_path))
    vk = PaymentVerificationKey.from_signing_key(sk)
    addr = Address(vk.hash(), network=Network.TESTNET)
    return sk, addr, skey_path


def main() -> None:
    sk, addr, skey_path = load_or_create()
    print("\n  Cardano PREPROD wallet ready (test funds only)")
    print("  " + "-" * 56)
    print(f"  signing key : {skey_path}  (gitignored)")
    print(f"  ADDRESS     : {addr}")
    print("  " + "-" * 56)
    print("  NEXT:")
    print("  1. Fund this address with test ADA:")
    print("     https://docs.cardano.org/cardano-testnets/tools/faucet")
    print("     -> select 'Preprod' -> paste the ADDRESS above -> request.")
    print("  2. Get a free PREPROD project id at https://blockfrost.io")
    print("     (Add project -> Cardano preprod) -> set BLOCKFROST_PROJECT_ID in .env")
    print("  3. Run:  python scripts/cardano_record.py")
    print()


if __name__ == "__main__":
    main()
