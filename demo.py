#!/usr/bin/env python3
"""
Quick Demo Script - Tests Persistent ChromaDB
Shows the speed difference between cached and non-cached startup
"""

import subprocess
import sys
import time
import shutil
from pathlib import Path


def clear_cache():
    """Remove the cache directory"""
    cache_dir = Path(".chroma")
    if cache_dir.exists():
        print("🧹 Clearing cache...")
        shutil.rmtree(cache_dir)
        print("✅ Cache cleared\n")


def run_chatbot_demo(test_name, clear_first=False):
    """Run chatbot and show startup time"""
    if clear_first:
        clear_cache()
    
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    print(f"⏱️  Starting chatbot...\n")
    
    # Start the chatbot
    proc = subprocess.Popen(
        [sys.executable, "chatbot.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    ready_time = None
    for line in proc.stdout:
        print(line.rstrip())
        
        # Mark when chatbot is ready for input
        if "🚀 RAG Chatbot Started!" in line:
            ready_time = time.time() - start_time
        
        # Stop after getting ready message
        if ready_time is not None:
            # Send a quit command
            proc.stdin.write("quit\n")
            proc.stdin.flush()
            # Read remaining output
            for remaining in proc.stdout:
                print(remaining, rstrip=True)
            break
    
    proc.wait()
    
    # Show timing results
    if ready_time:
        print(f"\n{'='*60}")
        print(f"⏱️  Ready in: {ready_time:.2f} seconds")
        print(f"{'='*60}\n")
        return ready_time
    else:
        print("\n⚠️ Could not measure time (did not reach ready state)")
        return None


def main():
    """Main demo"""
    print("\n" + "🎯 LIMMES CHATBOT - PERSISTENCE DEMO".center(60))
    print("="*60)
    
    # Check if PDF exists
    if not Path("your_doc.pdf").exists():
        print("\n⚠️  ERROR: your_doc.pdf not found!")
        print("\nPlease add a PDF file named 'your_doc.pdf' to test")
        print("\nSteps:")
        print("  1. Get a PDF file")
        print("  2. Rename it to 'your_doc.pdf'")
        print("  3. Place it in this directory")
        print("  4. Run this script again")
        return
    
    # Check if API key is set
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  ERROR: OPENAI_API_KEY not set!")
        print("\nPlease set your OpenAI API key:")
        print("  1. Create .env file (copy .env.example)")
        print("  2. Add: OPENAI_API_KEY=sk-xxxxx")
        print("  3. Run this script again")
        return
    
    print("\n✅ PDF found: your_doc.pdf")
    print("✅ API key configured")
    
    print("\n" + "="*60)
    print("DEMO PLAN:")
    print("="*60)
    print("\n1️⃣  First Run (SLOW - Creating Cache)")
    print("   - Loads PDF pages")
    print("   - Splits into chunks")
    print("   - Creates embeddings (calls OpenAI)")
    print("   - Saves to .chroma/ directory")
    print("   - Expected: 2-5 minutes")
    
    print("\n2️⃣  Second Run (FAST - Loading Cache)")
    print("   - Checks for .chroma/ directory")
    print("   - Loads cached embeddings from disk")
    print("   - No OpenAI calls needed")
    print("   - Expected: <1 second")
    
    print("\n" + "="*60)
    
    input("\n👉 Press ENTER to start Test 1 (first run)...")
    
    # Test 1: Clear cache and run
    time1 = run_chatbot_demo("TEST 1: First Run (No Cache)", clear_first=True)
    
    input("\n👉 Press ENTER to start Test 2 (second run)...")
    
    # Test 2: Run again with cache
    time2 = run_chatbot_demo("TEST 2: Second Run (With Cache)", clear_first=False)
    
    # Results
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)
    
    if time1 and time2:
        speedup = time1 / time2
        saved_time = time1 - time2
        
        print(f"\n⏱️  First run (no cache):   {time1:.2f} seconds")
        print(f"⏱️  Second run (cached):    {time2:.2f} seconds")
        print(f"🚀 Speedup:                {speedup:.1f}x faster")
        print(f"⏳ Time saved per restart:  {saved_time:.2f} seconds")
        
        # Cost calculation
        print("\n" + "-"*60)
        print("💰 COST ANALYSIS")
        print("-"*60)
        
        embedding_cost = 0.002  # Approximate for text-embedding-3-small
        
        print(f"\nCost per embedding call: ${embedding_cost}")
        print(f"\nScenario: 10 restarts per day (50 per week)")
        print(f"  Without persistence: 10 embeds/day = ${embedding_cost * 10:.4f}/day")
        print(f"  With persistence:    1 embed/month = ${embedding_cost / 30:.4f}/day")
        print(f"  Daily savings:       ${embedding_cost * (10 - 0.033):.4f}")
        print(f"  Monthly savings:     ${embedding_cost * 9.99:.2f}")
        print(f"  Annual savings:      ${embedding_cost * 119.7:.2f}")
        
        # Scale to multiple users
        print(f"\nFor a team of 10 users:")
        print(f"  Annual API savings:  ${embedding_cost * 119.7 * 10:.2f}")
        print(f"  Productivity gain:   {saved_time * 10 * 365 / 3600:.0f} hours/year")
    
    # Next steps
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("="*60)
    
    print("\n📚 Next Steps:")
    print("  1. Read PERSISTENCE.md for detailed docs")
    print("  2. Read SALES_GUIDE.md for selling tips")
    print("  3. Use TESTING.md for comprehensive tests")
    print("  4. Share benchmarks with potential customers")
    
    print("\n🚀 Ready to sell your chatbot!")
    print("   See SALES_GUIDE.md for pricing and positioning\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
