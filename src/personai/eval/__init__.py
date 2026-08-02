"""Evaluation harness — measure review quality against labeled fixtures.

Kept import-light on purpose: submodules are imported directly
(`personai.eval.scoring`, `.dataset`, `.runner`) so that the pure, offline
scoring/dataset code can be used without pulling in the reviewer (and Anthropic
SDK) that `runner` depends on.
"""
