# Terminology

Agreed terminology for the voting simulator and its documentation. Extend this
file as further terms are settled.

## Fair share

Use **fair share** for a party's or list's fractional seat entitlement: the
number of seats it would receive under exact proportionality, before rounding.

For a party in a single constituency, or nationally:

```text
fair share = total seats × party votes / total votes
```

For example, 27% of the votes with 10 seats gives a fair share of **2.7 seats**.
The fair share is a number of seats, whereas a **seat share** is a proportion
of seats. A fair share may happen to be an integer.

### Constituency and double scaling

- **Constituency fair share:** constituency seats × the list's proportion of
  constituency votes. Constituency seats include fixed and adjustment seats.
- **Doubly scaled fair share:** a fractional seat allocation obtained by scaling
  both rows and columns of the vote table so that the row sums match the
  specified constituency seat totals and the column sums match the specified
  party seat totals.

State which benchmark is intended when more than one is in use. These are
fractional benchmarks for assessing allocations; the allocated seats themselves
are integers.

### Allocation-method names

Use these names for the four related greedy adjustment-seat methods:

- **Maximum votes:** votes divided by the next divisor.
- **Maximum vote percentage:** constituency vote proportion divided by the next
  divisor.
- **Maximum fair share:** constituency fair share divided by the next divisor.
- **Norwegian weighted quotient:** constituency vote proportion weighted by
  fixed seats and divided by the next divisor. The implementation uses at least
  one as the fixed-seat weight.

Each method selects the largest eligible score. Omit “constituency” from the
dropdown names; explain the constituency basis and divisor in tooltips where
needed. The Maximum fair share tooltip should explicitly explain that the fair
share is a fractional number of seats. The regional selector uses the same names,
with the corresponding quantities calculated for regions.

### Literature

“Fair share” is established terminology, although authors also use “quota” or
“ideal share of seats”. Relevant examples include:

- Balinski and Young, *Fair Representation* (2001), pp.14–15: fair share,
  explicitly applicable to a state or party.
- Robinson and Ullman, *The Mathematics of Politics*, second edition (2017),
  pp.136–137: “fair share or standard quota”.
- Bredereck et al., [*How to tamper with a Parliament: Strategic campaigns in
  apportionment elections*](https://docserv.uni-duesseldorf.de/servlets/DerivateServlet/Derivate-76814/Rothe_How.pdf),
  p.6: a party's fractional seat entitlement.
- Martínez-Panero, Arredondo, Peña and Ramírez,
  [*A New Quota Approach to Electoral Disproportionality*](https://doi.org/10.3390/economies7010017)
  (2019), §§2 and 5: “quota” or “fair share”; both Loosemore–Hanby and Gallagher
  are expressed as deviations of allocated seats from these fractional counts.
- Ricca, Scozzari and Serafini, “The Mathematics of Seat Allocation and Political
  Districting”, in [*Trends in Computational Social Choice*](https://archive.illc.uva.nl/COST-IC1205/BookDocs/TrendsCOMSOC.pdf)
  (2017), pp.53–55: fair share in the doubly scaled sense.

Þorkell Helgason uses **sætahlutur** for the fractional entitlement, including
in his definitions of Loosemore–Hanby and Gallagher (*Fræðarinn*, §11.4, p.239).
