CRA Scope Notes
================

.. warning::

   This page describes facts relevant to EU Cyber Resilience Act (CRA,
   Regulation (EU) 2024/2847) scope assessment. **It is not a legal
   determination.** Whether MultiFlexi falls within CRA scope, and what
   obligations follow, should be confirmed with counsel once final European
   Commission guidance is published (expected later in 2026).

Deadlines
---------

Two dates matter regardless of final scope classification:

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Obligation
     - Date
     - Notes
   * - Reporting obligations
     - **11 September 2026**
     - Actively exploited vulnerabilities and severe incidents become
       subject to mandatory 24-hour notification to ENISA / the relevant
       national CSIRT, for in-scope manufacturers.
   * - Full conformity requirements
     - **11 December 2027**
     - Full CRA conformity (technical documentation, risk assessment,
       CE marking process, etc.) applies to in-scope products.

These are recorded here so they're visible in-repo rather than only in
planning conversations.

Monetization vectors (as of this audit, 2026-07)
---------------------------------------------------

Pure community open-source publishing, with no monetization, likely falls
outside "placing on the market" under the CRA. MultiFlexi currently has two
vectors that plausibly bring parts of the project into scope as a
"manufacturer":

1. **Hardware appliances.** MultiFlexi is sold pre-installed on Raspberry Pi
   hardware in multiple tiers (Lite, Standard, Pro, Enterprise). The
   Raspberry Pi hardware itself is sourced from multiple suppliers as part
   of building these appliances. Software bundled with hardware and placed
   on the market is unambiguously in scope for CRA purposes — this is the
   clearer of the two vectors.
2. **A possible future subscription/support model.** Not yet in effect. If
   introduced, whether it brings the software into "placing on the market"
   scope depends on the Commission's "monetization test" (draft guidance,
   March 2026) — see below.

The "monetization test" concept
------------------------------------

The European Commission's draft guidance (March 2026) proposes a test for
whether making software available in connection with some form of
monetization counts as "placing on the market" under the CRA, as distinct
from pure non-commercial open-source distribution. This is draft guidance,
not final at the time of writing — treat any interpretation of it as
provisional until the Commission publishes final guidance (expected later
in 2026).

.. note::

   This page intentionally does not attempt to apply the monetization test
   to MultiFlexi's specific facts, or conclude whether MultiFlexi "is" or
   "is not" in CRA scope. That determination should be made with counsel
   once final guidance is available.

Relationship to the SBOM process
-------------------------------------

An SBOM is a prerequisite for any CRA compliance path, and for the 24-hour
vulnerability reporting obligation specifically — a project cannot report on
vulnerable dependencies it hasn't inventoried. See :doc:`sbom-process` for
how MultiFlexi generates and maintains SBOMs across its repositories. This
work proceeds independently of the final scope determination, since an
accurate dependency inventory is good practice regardless of CRA
applicability.
