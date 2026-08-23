"""Strategies (PROJECT_SPEC.md §6, §7).

Bot A and Bot B are separate implementations with separate configuration, per PROJECT_SPEC.md
§7 ("Bot B is therefore NOT merely Bot A with a lower threshold") and §10.7. They deliberately
share no base class, so that neither can drift into being a parameterisation of the other.

Bot C (PROJECT_SPEC.md §8) is future architecture and is not present here.
"""
