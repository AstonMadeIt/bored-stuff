#!/usr/bin/env python3
"""
Update Game Results - Automated Validation
Fetches actual game results and updates predictions
Run nightly after games complete (11pm cron job)
"""

import sys
from datetime import datetime, timedelta
from automated_validation_system import AutomatedValidationSystem

def update_results_for_date(date_str=None):
    """Update results for a specific date (default: yesterday)"""
    
    if date_str is None:
        # Default to yesterday (games finish late)
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d')
    
    print("="*80)
    print("📊 AUTOMATED VALIDATION - UPDATING RESULTS")
    print("="*80)
    print(f"Date: {date_str}")
    print("")
    
    system = AutomatedValidationSystem()
    
    # Update results
    updated_count = system.update_results(date_str)
    
    if updated_count > 0:
        # Calculate performance summary
        print("\n📈 Calculating performance summary...")
        summary = system.calculate_performance_summary(date_str)
        
        if summary:
            print(f"   ✅ {summary['sport'] or 'Overall'}: {summary['correct']}/{summary['total']} ({summary['win_rate']*100:.1f}%)")
            if summary['high_confidence']['total'] > 0:
                hc = summary['high_confidence']
                print(f"   🔥 High Confidence: {hc['correct']}/{hc['total']} ({hc['win_rate']*100:.1f}%)")
            if summary['high_divergence']['total'] > 0:
                hd = summary['high_divergence']
                print(f"   💰 High Divergence: {hd['correct']}/{hd['total']} ({hd['win_rate']*100:.1f}%)")
        
        # Regenerate results pages
        print("\n📄 Regenerating results pages...")
        try:
            from generate_results_pages import generate_all_results_pages
            generate_all_results_pages()
            print("   ✅ Results pages updated")
        except ImportError:
            print("   ⚠️  Results page generator not found")
        except Exception as e:
            print(f"   ⚠️  Error generating pages: {e}")
    else:
        print("   ⚠️  No games to update (may not be completed yet)")
    
    print("\n✅ Validation update complete!")
    return updated_count

if __name__ == '__main__':
    # Allow date override: python3 update_results.py 2025-12-29
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    update_results_for_date(date_arg)


