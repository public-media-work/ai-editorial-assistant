# Check Model Pricing

Verify LLM pricing is up-to-date and re-evaluate model priority order.

## Your Task

1. Run the pricing verification script
2. Display the pricing summary and recommendations
3. Review the current auto_select order in llm-config.json
4. Recommend updates if pricing has changed significantly

## How This Works

### Step 1: Run Pricing Check

Execute the pricing verification script:

```bash
python3 scripts/check_pricing.py
```

This will:
- Check all pricing constants against documented sources
- Rank models by cost/performance
- Show current configuration
- Log results to `logs/pricing_check.log`

### Step 2: Review Configuration

Read and display the current configuration from `config/llm-config.json`:
- Current `auto_select.preference_order`
- Current `BACKEND_PREFERENCES` from processing scripts

### Step 3: Analyze and Recommend

Based on the pricing check output:
1. Identify if any pricing has changed
2. Evaluate if the current model priority order is still optimal
3. Provide specific recommendations for updates if needed

### Step 4: Optionally Update

If pricing has changed and the user approves:
1. Update pricing constants in `scripts/llm_backend.py`
2. Update "Last updated" date in comments
3. Adjust `auto_select.preference_order` if needed
4. Explain the rationale for any changes

## Expected Output

Show the user:
- ✅ Pricing verification summary
- 📊 Model rankings by cost
- ⚙️ Current auto_select configuration
- 💡 Recommendations (if any changes needed)
- 📝 Log location for future reference

## Notes

- This should be run monthly or when you suspect pricing changes
- Major pricing changes should trigger an update to the config
- Always explain the reasoning behind recommended changes
- Update the "Last updated" dates when pricing constants change
