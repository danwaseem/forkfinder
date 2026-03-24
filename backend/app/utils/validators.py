"""
Reusable validators for profile fields.

Exported helpers:
  normalize_country(value)        — case-insensitive lookup, returns canonical name
  validate_us_state(state, country) — raises ValueError if country is US and state is invalid
  PHONE_RE                        — compiled regex for phone numbers
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# US state / territory abbreviations
# ---------------------------------------------------------------------------

US_STATES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
    # Federal district + territories
    "DC": "District of Columbia",
    "PR": "Puerto Rico", "GU": "Guam", "VI": "U.S. Virgin Islands",
    "AS": "American Samoa", "MP": "Northern Mariana Islands",
}

# Names and aliases recognised as "United States"
_US_ALIASES: frozenset[str] = frozenset({
    "united states", "united states of america",
    "us", "usa", "u.s.", "u.s.a.",
})

# ---------------------------------------------------------------------------
# Country list (canonical names — title-cased)
# ---------------------------------------------------------------------------

COUNTRIES: frozenset[str] = frozenset({
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina",
    "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
    "Bangladesh", "Belarus", "Belgium", "Belize", "Benin", "Bolivia",
    "Bosnia and Herzegovina", "Brazil", "Bulgaria", "Cambodia", "Cameroon",
    "Canada", "Chile", "China", "Colombia", "Costa Rica", "Croatia", "Cuba",
    "Cyprus", "Czech Republic", "Denmark", "Dominican Republic", "Ecuador",
    "Egypt", "El Salvador", "Estonia", "Ethiopia", "Finland", "France",
    "Georgia", "Germany", "Ghana", "Greece", "Guatemala", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya",
    "Kuwait", "Latvia", "Lebanon", "Libya", "Lithuania", "Luxembourg",
    "Malaysia", "Malta", "Mexico", "Moldova", "Morocco", "Mozambique",
    "Myanmar", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Nigeria",
    "North Korea", "Norway", "Oman", "Pakistan", "Panama", "Paraguay", "Peru",
    "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia",
    "Saudi Arabia", "Senegal", "Serbia", "Singapore", "Slovakia", "Slovenia",
    "Somalia", "South Africa", "South Korea", "Spain", "Sri Lanka", "Sudan",
    "Sweden", "Switzerland", "Syria", "Taiwan", "Tanzania", "Thailand",
    "Tunisia", "Turkey", "Uganda", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Venezuela",
    "Vietnam", "Yemen", "Zimbabwe",
})

# Pre-build a lowercase → canonical mapping for O(1) case-insensitive lookup
_COUNTRY_LOWER: dict[str, str] = {c.lower(): c for c in COUNTRIES}

# ---------------------------------------------------------------------------
# Phone number pattern
# ---------------------------------------------------------------------------

# Accepts: +1 (800) 555-0100 / 800-555-0100 / +44 20 7946 0958 / etc.
PHONE_RE: re.Pattern = re.compile(r"^[+\d][\d\s\-().]{5,29}$")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def normalize_country(value: str) -> str:
    """
    Return the canonical country name for *value*.

    Raises ``ValueError`` if the country is not recognised.
    Accepts any capitalisation (e.g. "united states", "FRANCE", "france").
    """
    key = value.strip().lower()
    canonical = _COUNTRY_LOWER.get(key)
    if canonical is None:
        raise ValueError(
            f'"{value}" is not a recognised country name. '
            "Use a standard English country name (e.g. \"United States\", \"France\")."
        )
    return canonical


def validate_us_state(state: Optional[str], country: Optional[str]) -> None:
    """
    When *country* resolves to the United States, enforce that *state* is a
    valid 2-letter USPS abbreviation (e.g. "CA", "NY").

    Does nothing when country is not the US or when either argument is None.
    Raises ``ValueError`` on failure.
    """
    if state is None or country is None:
        return
    if country.strip().lower() not in _US_ALIASES and country != "United States":
        return  # Non-US country — free-form state is fine

    abbr = state.strip().upper()
    if abbr not in US_STATES:
        valid = ", ".join(sorted(US_STATES))
        raise ValueError(
            f'"{state}" is not a valid US state abbreviation. '
            f"Expected one of: {valid}."
        )
