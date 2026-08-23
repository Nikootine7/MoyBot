"""Immutable domain types.

Vocabulary is Solana-shaped per docs/DECISIONS.md D-001: a token is identified by its mint
address, holders are token-account owners, "dev" refers to the mint/update authority or
deployer, and every snapshot carries both a wall-clock millisecond timestamp and a slot,
because slot is the only sound ordering key on Solana.
"""
