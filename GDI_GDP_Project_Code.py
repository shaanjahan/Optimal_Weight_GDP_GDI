"""
Optimal Weight Gross Domestic Product and Gross Domestic Income: Productivity Calculation
By: Lamae A. Maharaj 
Feb 2026.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from fredapi import Fred
import time
import os
from pathlib import Path

API_KEY = "cb13b116bf78b290ea691bbf95c189bf"  

def get_output_dir():
    """Find a writable directory for outputs."""
    possible_dirs = [
        os.path.expanduser("~/gdp_gdi_output"), 
        "/tmp/gdp_gdi_output",  
        "."  
    ]
    
    for directory in possible_dirs:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            # Test if writable
            test_file = Path(directory) / ".test"
            test_file.touch()
            test_file.unlink()
            print(f"Output directory: {directory}")
            return directory
        except:
            continue
    
    print("Warning: No writable directory found. Results will display only.")
    return None

OUTPUT_DIR = '/Users/lamaemaharaj/Desktop/Economics Projects/GDP_GDI_Project'

# Downloading Data

print("="*70)
print("PART 0: DOWNLOADING DATA FROM FRED")
print("="*70)

fred = Fred(api_key=API_KEY)

print("\n1. Downloading GDP vintages...")
try:
    gdp_vintages_raw = fred.get_series_all_releases('GDP', realtime_start='1990-01-01')
    gdp_vintages = gdp_vintages_raw.pivot(index='date', columns='realtime_start', values='value')
    print(f"   ✓ Got {gdp_vintages.shape[1]} GDP vintages covering {gdp_vintages.shape[0]} quarters")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

time.sleep(1)

print("\n2. Downloading GDI vintages...")
try:
    gdi_vintages_raw = fred.get_series_all_releases('GDI', realtime_start='1990-01-01')
    gdi_vintages = gdi_vintages_raw.pivot(index='date', columns='realtime_start', values='value')
    print(f"   ✓ Got {gdi_vintages.shape[1]} GDI vintages covering {gdi_vintages.shape[0]} quarters")
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

time.sleep(1)

print("\n3. Downloading current data series...")
gdp_current = fred.get_series('GDP', observation_start='1990-01-01')
gdi_current = fred.get_series('GDI', observation_start='1990-01-01')
productivity = fred.get_series('OPHNFB', observation_start='1990-01-01')
hours = fred.get_series('HOANBS', observation_start='1990-01-01')

print(f"   ✓ GDP current: {len(gdp_current)} observations")
print(f"   ✓ GDI current: {len(gdi_current)} observations")
print(f"   ✓ Productivity: {len(productivity)} observations")
print(f"   ✓ Hours: {len(hours)} observations")

print("\nData download complete!")

# Revision Analysis

print("\n" + "="*70)
print("PART 1: COMPUTING REVISIONS AND ERROR VARIANCES")
print("="*70)

class RevisionAnalyzer:
    """Calculate revisions from vintage data."""
    
    def __init__(self, vintages_df):
        self.vintages = vintages_df
        
    def get_initial_estimate(self):
        """Get first published value for each observation."""
        initial = pd.Series(index=self.vintages.index, dtype=float)
        
        for obs_date in self.vintages.index:
            available = self.vintages.loc[obs_date].dropna()
            if len(available) > 0:
                initial.loc[obs_date] = available.iloc[0]
        
        return initial.dropna()
    
    def get_final_estimate(self):
        """Get most recent value for each observation."""
        final = self.vintages.apply(
            lambda row: row.dropna().iloc[-1] if len(row.dropna()) > 0 else np.nan, 
            axis=1
        )
        return final.dropna()
    
    def compute_growth_rate_revisions(self):
        """Compute revisions to growth rates."""
        initial = self.get_initial_estimate()
        final = self.get_final_estimate()
        
        common = initial.index.intersection(final.index)
        initial = initial.loc[common]
        final = final.loc[common]
        
        print(f"  Computing growth rates for {len(common)} observations")
        
        initial_growth = 400 * np.log(initial / initial.shift(1))
        final_growth = 400 * np.log(final / final.shift(1))
        
        revisions = final_growth - initial_growth
        
        return revisions.dropna()


print("\nAnalyzing GDP revisions...")
gdp_analyzer = RevisionAnalyzer(gdp_vintages)
gdp_growth_revisions = gdp_analyzer.compute_growth_rate_revisions()

print("\nAnalyzing GDI revisions...")
gdi_analyzer = RevisionAnalyzer(gdi_vintages)
gdi_growth_revisions = gdi_analyzer.compute_growth_rate_revisions()

gdp_sigma = gdp_growth_revisions.std()
gdi_sigma = gdi_growth_revisions.std()

common_dates = gdp_growth_revisions.index.intersection(gdi_growth_revisions.index)
gdp_aligned = gdp_growth_revisions.loc[common_dates]
gdi_aligned = gdi_growth_revisions.loc[common_dates]
rho = gdp_aligned.corr(gdi_aligned)

print("\n" + "-"*70)
print("REVISION STATISTICS (Growth Rates)")
print("-"*70)
print(f"GDP standard deviation:  {gdp_sigma:.3f} percentage points")
print(f"GDI standard deviation:  {gdi_sigma:.3f} percentage points")
print(f"Correlation (rho):       {rho:.3f}")
print(f"Number of observations:  {len(common_dates)}")
print("-"*70)

print("\nComparison to Nalewaik (2010):")
print(f"  Nalewaik: GDP σ ≈ 3.0, GDI σ ≈ 2.3")
print(f"  Our data: GDP σ = {gdp_sigma:.3f}, GDI σ = {gdi_sigma:.3f}")

if gdi_sigma < gdp_sigma:
    print(f"\n✓ Confirms Nalewaik: GDI has lower variance than GDP")
else:
    print(f"\n⚠ Different from Nalewaik in our sample period")

# Optimal Weight Calculations

print("\n" + "="*70)
print("PART 2: COMPUTING OPTIMAL WEIGHTS")
print("="*70)

def compute_optimal_weight(sigma_u, sigma_v, rho=0):
    """Calculate optimal weight on GDP."""
    sigma_u_sq = sigma_u ** 2
    sigma_v_sq = sigma_v ** 2
    
    if abs(rho) < 0.001:
        return sigma_v_sq / (sigma_u_sq + sigma_v_sq)
    else:
        numerator = sigma_v_sq - rho * sigma_u * sigma_v
        denominator = sigma_u_sq + sigma_v_sq - 2 * rho * sigma_u * sigma_v
        return numerator / denominator


lambda_opt_uncorr = compute_optimal_weight(gdp_sigma, gdi_sigma, rho=0)
lambda_opt_corr = compute_optimal_weight(gdp_sigma, gdi_sigma, rho=rho)

print("\nOPTIMAL WEIGHTS:")
print("-"*70)
print("\nAssuming uncorrelated errors (ρ = 0):")
print(f"  Weight on GDP: {lambda_opt_uncorr:.3f} ({lambda_opt_uncorr*100:.1f}%)")
print(f"  Weight on GDI: {1-lambda_opt_uncorr:.3f} ({(1-lambda_opt_uncorr)*100:.1f}%)")

print(f"\nWith estimated correlation (ρ = {rho:.3f}):")
print(f"  Weight on GDP: {lambda_opt_corr:.3f} ({lambda_opt_corr*100:.1f}%)")
print(f"  Weight on GDI: {1-lambda_opt_corr:.3f} ({(1-lambda_opt_corr)*100:.1f}%)")

print("\nComparison to alternatives:")
print(f"  BLS (100% GDP):  100% GDP, 0% GDI")
print(f"  BEA average:     50% GDP, 50% GDI")
print(f"  Our optimal:     {lambda_opt_corr*100:.1f}% GDP, {(1-lambda_opt_corr)*100:.1f}% GDI")
print("-"*70)

lambda_optimal = lambda_opt_corr


# Output Series Creation

print("\n" + "="*70)
print("PART 3: CONSTRUCTING OUTPUT SERIES")
print("="*70)

common_dates = gdp_current.index.intersection(gdi_current.index)
gdp_aligned_output = gdp_current.loc[common_dates]
gdi_aligned_output = gdi_current.loc[common_dates]

output_gdp = gdp_aligned_output
output_bea_avg = 0.5 * gdp_aligned_output + 0.5 * gdi_aligned_output
output_optimal = lambda_optimal * gdp_aligned_output + (1 - lambda_optimal) * gdi_aligned_output

print(f"\nConstructed three output series:")
print(f"  1. GDP only (BLS method)")
print(f"  2. BEA average (50-50)")
print(f"  3. Optimal weighted ({lambda_optimal*100:.1f}% GDP, {(1-lambda_optimal)*100:.1f}% GDI)")
print(f"\n{len(output_gdp)} observations from {output_gdp.index[0]} to {output_gdp.index[-1]}")

# PART 4: COMPUTE PRODUCTIVITY

print("\n" + "="*70)
print("PART 4: COMPUTING LABOR PRODUCTIVITY")
print("="*70)

hours_aligned = hours.loc[common_dates]

productivity_gdp = output_gdp / hours_aligned
productivity_bea = output_bea_avg / hours_aligned
productivity_opt = output_optimal / hours_aligned

def compute_growth(series):
    return 400 * np.log(series / series.shift(1))

growth_gdp = compute_growth(productivity_gdp).dropna()
growth_bea = compute_growth(productivity_bea).dropna()
growth_opt = compute_growth(productivity_opt).dropna()
growth_bls = compute_growth(productivity.loc[common_dates]).dropna()

print(f"\nComputed productivity growth rates")
print(f"Sample: {growth_gdp.index[0]} to {growth_gdp.index[-1]}")

# Results

print("\n" + "="*70)
print("PART 5: RESULTS")
print("="*70)

print("\nAVERAGE ANNUAL PRODUCTIVITY GROWTH:")
print("-"*70)
print(f"BLS official:      {growth_bls.mean():.2f}%")
print(f"GDP-based:         {growth_gdp.mean():.2f}%")
print(f"BEA average:       {growth_bea.mean():.2f}%")
print(f"Optimal weighted:  {growth_opt.mean():.2f}%")
print("-"*70)

diff_opt_gdp = growth_opt - growth_gdp
diff_opt_bls = growth_opt - growth_bls

print("\nDIFFERENCE: OPTIMAL vs GDP-BASED:")
print(f"  Mean:    {diff_opt_gdp.mean():.3f} pp")
print(f"  Std:     {diff_opt_gdp.std():.3f} pp")
print(f"  Max:     {diff_opt_gdp.max():.3f} pp")
print(f"  Min:     {diff_opt_gdp.min():.3f} pp")

print("\nDIFFERENCE: OPTIMAL vs BLS:")
print(f"  Mean:        {diff_opt_bls.mean():.3f} pp")
print(f"  Correlation: {growth_opt.corr(growth_bls):.3f}")

# Sub-period analysis
print("\n" + "-"*70)
print("SUB-PERIOD ANALYSIS")
print("-"*70)

periods = {
    'Pre-crisis (1990-2007)': ('1990', '2007'),
    'Financial crisis (2008-2009)': ('2008', '2009'),
    'Recovery (2010-2019)': ('2010', '2019'),
    'COVID era (2020-2024)': ('2020', '2024')
}

for period_name, (start, end) in periods.items():
    mask = (growth_opt.index.year >= int(start)) & (growth_opt.index.year <= int(end))
    
    if mask.sum() > 0:
        avg_gdp = growth_gdp.loc[mask].mean()
        avg_opt = growth_opt.loc[mask].mean()
        diff = avg_opt - avg_gdp
        
        print(f"\n{period_name}:")
        print(f"  GDP-based: {avg_gdp:6.2f}%")
        print(f"  Optimal:   {avg_opt:6.2f}%")
        print(f"  Diff:      {diff:+6.2f} pp")

# Saving Results

print("\n" + "="*70)
print("PART 6: SAVING RESULTS")
print("="*70)

# Create results dataframes (in memory always)
results_df = pd.DataFrame({
    'GDP_based': growth_gdp,
    'BEA_average': growth_bea,
    'Optimal': growth_opt,
    'BLS_official': growth_bls,
    'Diff_Optimal_GDP': diff_opt_gdp,
    'Diff_Optimal_BLS': diff_opt_bls
})

summary = pd.DataFrame({
    'Measure': ['GDP-based', 'BEA average', 'Optimal', 'BLS official'],
    'Mean': [growth_gdp.mean(), growth_bea.mean(), growth_opt.mean(), growth_bls.mean()],
    'Std': [growth_gdp.std(), growth_bea.std(), growth_opt.std(), growth_bls.std()]
})

params = pd.DataFrame({
    'Parameter': ['sigma_u_GDP', 'sigma_v_GDI', 'rho', 'lambda_optimal', 'weight_GDP_%', 'weight_GDI_%'],
    'Value': [gdp_sigma, gdi_sigma, rho, lambda_optimal, lambda_optimal*100, (1-lambda_optimal)*100]
})

# Try to save if we have a writable directory
if OUTPUT_DIR:
    try:
        results_df.to_csv(Path(OUTPUT_DIR) / 'productivity_growth_results.csv')
        print(f"  ✓ Saved: {OUTPUT_DIR}/productivity_growth_results.csv")
        
        summary.to_csv(Path(OUTPUT_DIR) / 'summary_statistics.csv', index=False)
        print(f"  ✓ Saved: {OUTPUT_DIR}/summary_statistics.csv")
        
        params.to_csv(Path(OUTPUT_DIR) / 'parameter_estimates.csv', index=False)
        print(f"  ✓ Saved: {OUTPUT_DIR}/parameter_estimates.csv")
    except Exception as e:
        print(f"  ⚠ Could not save files: {e}")
        print("  → Results available in memory as: results_df, summary, params")
else:
    print("  → Results available in memory as: results_df, summary, params")

# Display the key tables
print("\n" + "-"*70)
print("SUMMARY STATISTICS (in memory)")
print("-"*70)
print(summary.to_string(index=False))

print("\n" + "-"*70)
print("PARAMETER ESTIMATES (in memory)")
print("-"*70)
print(params.to_string(index=False))

# Data Visualizations

print("\n" + "="*70)
print("PART 7: CREATING VISUALIZATIONS")
print("="*70)

plt.style.use('seaborn-v0_8-darkgrid')

# Productivity growth over time
fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(growth_gdp.index, growth_gdp, label='GDP-based', alpha=0.7, linewidth=1.5)
ax.plot(growth_bea.index, growth_bea, label='BEA 50-50', alpha=0.7, linewidth=1.5)
ax.plot(growth_opt.index, growth_opt, label='Optimal', alpha=0.9, linewidth=2)
ax.plot(growth_bls.index, growth_bls, label='BLS official', alpha=0.5, linestyle='--')

ax.axhline(0, color='black', linewidth=0.5)
ax.set_xlabel('Year')
ax.set_ylabel('Productivity Growth Rate (%)')
ax.set_title('Labor Productivity Growth: Comparing Output Measures')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
if OUTPUT_DIR:
    try:
        plt.savefig(Path(OUTPUT_DIR) / 'productivity_comparison.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {OUTPUT_DIR}/productivity_comparison.png")
    except:
        print("  ⚠ Could not save plot")
plt.show()

# Differences
fig, ax = plt.subplots(figsize=(14, 5))

ax.plot(diff_opt_gdp.index, diff_opt_gdp, linewidth=1.5, color='darkblue')
ax.fill_between(diff_opt_gdp.index, 0, diff_opt_gdp, alpha=0.3)
ax.axhline(0, color='red', linewidth=1, linestyle='--')
ax.axhline(diff_opt_gdp.mean(), color='orange', linewidth=2, linestyle='--', 
           label=f'Mean = {diff_opt_gdp.mean():.3f} pp')
ax.set_xlabel('Year')
ax.set_ylabel('Difference (percentage points)')
ax.set_title('Productivity Growth Difference: Optimal vs GDP-based')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
if OUTPUT_DIR:
    try:
        plt.savefig(Path(OUTPUT_DIR) / 'productivity_difference.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {OUTPUT_DIR}/productivity_difference.png")
    except:
        pass
plt.show()

# Final Summary

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)

print("\nKEY FINDINGS:")
print(f"1. {'GDI' if gdi_sigma < gdp_sigma else 'GDP'} has lower measurement error")
print(f"   (σ_GDI = {gdi_sigma:.3f} vs σ_GDP = {gdp_sigma:.3f})")

print(f"\n2. Optimal weight: {lambda_optimal*100:.1f}% GDP, {(1-lambda_optimal)*100:.1f}% GDI")

print(f"\n3. Average productivity difference: {diff_opt_gdp.mean():.3f} pp")

if OUTPUT_DIR:
    print(f"\nFiles saved to: {OUTPUT_DIR}")
else:
    print("\nResults available in memory:")
    print("  • results_df - full productivity growth time series")
    print("  • summary - summary statistics table")
    print("  • params - parameter estimates")

print("\n" + "="*70)
