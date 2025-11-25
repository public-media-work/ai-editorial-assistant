# Deliverable Validation Checklist

## Automated Checks (Performed by CLI Agent)

### Format Validation
- [ ] All required sections present in correct order
- [ ] All markdown tables properly formatted
- [ ] All placeholder brackets `[PLACEHOLDER]` have been replaced
- [ ] No template artifacts remaining in output

### Content Validation
- [ ] All character counts are EXACT (including spaces)
- [ ] Character counts in "Character Count" columns match actual content
- [ ] Title length ≤ 80 characters
- [ ] Short description length ≤ 100 characters
- [ ] Long description length ≤ 350 characters
- [ ] Exactly 20 keywords provided (10 direct, 10 implied)

### Style Compliance
- [ ] No prohibited language detected (discover, learn, explore, watch as, see how, will show, will teach, amazing, incredible, don't miss, join us)
- [ ] Down style applied to titles (only first word and proper nouns capitalized)
- [ ] No dashes/colons in titles (except necessary apostrophes/quotes)
- [ ] AP Style abbreviation rules followed

### Program-Specific Rules
- [ ] University Place: No honorifics, series name in keywords (if applicable)
- [ ] Here & Now: Proper title format [SUBJECT] on [topic] (if applicable)
- [ ] The Look Back: Educational journey format with hosts/institutions (if applicable)

### Completeness
- [ ] Collaboration disclosure present
- [ ] Date stamp included
- [ ] Transcript filename referenced
- [ ] All table cells populated (no empty cells)

---

## Manual Review Prompts (For Human Editor)

### Editorial Judgment
- Does the content accurately reflect the transcript?
- Are title/short description pairings cohesive?
- Do keywords capture both explicit and conceptual themes?
- Is tone appropriate for PBS Wisconsin brand?

### Factual Verification
- Are all quotes accurate and properly attributed?
- Are speaker names/titles correct?
- Are institutional affiliations accurate?

### SEO Effectiveness
- Do keywords align with likely search intent?
- Is long description compelling without being promotional?
- Are there opportunities for trending topic alignment?

---

## Validation Failed - Common Issues

**Character Count Mismatch:**
- STOP: Recount manually, verify spaces included
- Update both content and count column

**Prohibited Language Detected:**
- STOP: Rewrite affected section using factual framing
- Document original version in revision notes

**Missing Required Sections:**
- STOP: Fill missing section using appropriate template
- Verify all placeholders replaced

**Table Formatting Broken:**
- STOP: Re-apply template structure
- Verify markdown rendering in preview

---

## Sign-Off

**Automated Validation:** [PASS/FAIL]
**Manual Review Required:** [YES - Human editor must verify editorial judgment]
**Ready for Delivery:** [YES/NO]

**Validator:** Claude Code CLI Agent
**Validation Date:** [DATE]
**Deliverable:** [FILENAME]
