### overview

Code for intranet webapp producing Tech Services reports for staff.

Note: not reflected in the commit history here is that all this code was written by [Ted Lawless](https://github.com/lawlesst).

[I'm](https://github.com/birkin) just updating it here with tweaks for python3, a newer version of django, and some architectural changes.

---

### stats description

#### viewing the webapp

When you click on an Accession -> Accessions by month -> the-month, here's what happens...

- The 'start' and 'end' dates for the month are created.

- Accession records stored in a database are retrieved that are greater-than-or-equal-to the start date, _and_ less-than-or-equal-to the end date.
    - You can see what an Accession record looks like via the admin.

- SummaryAccession records stored in a database are also retrieved the same way.
    - You can see what a SummaryAccession record looks like via the admin.

- A list containing both records is created.
    - Q: why? There is subsequent processing done on this combined list. Though some of the fields are the same, the two types of records seem different. I would have thought that a SummaryAccession record contains totals for the Accession records, but the April totals do not bear that out.

- Counts based on Accession records are performed.


---

#### processing the marc-records

- description coming

---
