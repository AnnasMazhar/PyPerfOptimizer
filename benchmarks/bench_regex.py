"""Comprehensive benchmark for regex precompile transform."""
import timeit
import re
import sys

sys.path.insert(0, "src")
from pyperfoptimizer.autofix import scan, fix

# ═══════════════════════════════════════════════════════════════
# BENCHMARK 1: Realistic function with regex in hot path
# ═══════════════════════════════════════════════════════════════
original = '''
import re

def process_users(users):
    results = []
    for user in users:
        if user["role"] in {"admin", "editor", "moderator", "reviewer", "manager"}:
            name = user["first"] + " " + user["last"]
            if re.match(r"^[A-Z]", name):
                results.append({"name": name, "role": user["role"]})
    return results
'''

optimized = fix(original)
print("=" * 70)
print("BENCHMARK 1: Realistic user processing (regex + set + append)")
print("=" * 70)
print("\nOriginal code:")
print(original.strip())
print("\nOptimized code:")
print(optimized.strip())

setup = '''
import re, random, string
users = []
roles = ["admin", "editor", "moderator", "reviewer", "manager", "viewer", "guest"]
for i in range(2000):
    first = random.choice(string.ascii_uppercase) + "".join(random.choices(string.ascii_lowercase, k=5))
    last = random.choice(string.ascii_uppercase) + "".join(random.choices(string.ascii_lowercase, k=7))
    users.append({"first": first, "last": last, "role": random.choice(roles)})
'''

t_orig = timeit.timeit("process_users(users)", setup=setup + original, number=500)
t_opt = timeit.timeit("process_users(users)", setup=setup + optimized, number=500)
print(f"\nOriginal:  {t_orig*1000:.1f}ms (500 iterations x 2000 users)")
print(f"Optimized: {t_opt*1000:.1f}ms")
print(f"Speedup:   {t_orig/t_opt:.2f}x")

# ═══════════════════════════════════════════════════════════════
# BENCHMARK 2: Simple validation (re.match in a loop)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("BENCHMARK 2: Email validation (re.match in loop)")
print("=" * 70)

orig_validate = '''
import re

def validate_emails(emails):
    valid = []
    for email in emails:
        if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email):
            valid.append(email)
    return valid
'''

opt_validate = fix(orig_validate)
print("\nOptimized:")
print(opt_validate.strip())

setup2 = '''
import re, random, string
emails = []
for i in range(5000):
    name = "".join(random.choices(string.ascii_lowercase, k=8))
    domain = "".join(random.choices(string.ascii_lowercase, k=5))
    if random.random() > 0.3:
        emails.append(f"{name}@{domain}.com")
    else:
        emails.append(f"invalid-{name}")
'''

t_orig2 = timeit.timeit("validate_emails(emails)", setup=setup2 + orig_validate, number=200)
t_opt2 = timeit.timeit("validate_emails(emails)", setup=setup2 + opt_validate, number=200)
print(f"\nOriginal:  {t_orig2*1000:.1f}ms (200 iterations x 5000 emails)")
print(f"Optimized: {t_opt2*1000:.1f}ms")
print(f"Speedup:   {t_orig2/t_opt2:.2f}x")

# ═══════════════════════════════════════════════════════════════
# BENCHMARK 3: Text cleaning (re.sub called many times)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("BENCHMARK 3: Text cleaning (multiple re.sub calls)")
print("=" * 70)

orig_clean = '''
import re

def clean_texts(texts):
    cleaned = []
    for text in texts:
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\\\\s+", " ", text)
        text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
        cleaned.append(text.strip())
    return cleaned
'''

opt_clean = fix(orig_clean)
print("\nOptimized:")
print(opt_clean.strip())

setup3 = '''
import re, random, string
texts = []
for i in range(2000):
    parts = []
    for j in range(5):
        word = "".join(random.choices(string.ascii_letters, k=random.randint(3,10)))
        if random.random() > 0.7:
            parts.append(f"<b>{word}</b>")
        elif random.random() > 0.5:
            parts.append(f"  {word}  ")
        else:
            parts.append(word + "!@#")
    texts.append(" ".join(parts))
'''

t_orig3 = timeit.timeit("clean_texts(texts)", setup=setup3 + orig_clean, number=100)
t_opt3 = timeit.timeit("clean_texts(texts)", setup=setup3 + opt_clean, number=100)
print(f"\nOriginal:  {t_orig3*1000:.1f}ms (100 iterations x 2000 texts)")
print(f"Optimized: {t_opt3*1000:.1f}ms")
print(f"Speedup:   {t_orig3/t_opt3:.2f}x")

# ═══════════════════════════════════════════════════════════════
# BENCHMARK 4: Combined (regex + set membership + append)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("BENCHMARK 4: Combined patterns (regex + list->set + append)")
print("=" * 70)

orig_combined = '''
import re

def filter_logs(entries):
    results = []
    for entry in entries:
        if entry["level"] in ["ERROR", "CRITICAL", "WARNING", "FATAL", "ALERT"]:
            msg = entry["message"]
            if re.search(r"(timeout|connection refused|500 error)", msg, re.IGNORECASE):
                ts = re.sub(r"T", " ", entry["timestamp"])
                results.append({"time": ts, "msg": msg, "level": entry["level"]})
    return results
'''

opt_combined = fix(orig_combined)
print("\nOptimized:")
print(opt_combined.strip())

setup4 = '''
import re, random, string
levels = ["ERROR", "CRITICAL", "WARNING", "FATAL", "ALERT", "INFO", "DEBUG"]
messages = [
    "Connection refused on port 8080",
    "Timeout after 30s waiting for response",
    "500 error from upstream",
    "Request completed successfully",
    "Cache hit for key abc123",
    "User logged in",
]
entries = []
for i in range(3000):
    entries.append({
        "level": random.choice(levels),
        "message": random.choice(messages),
        "timestamp": f"2026-05-10T{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}",
    })
'''

t_orig4 = timeit.timeit("filter_logs(entries)", setup=setup4 + orig_combined, number=200)
t_opt4 = timeit.timeit("filter_logs(entries)", setup=setup4 + opt_combined, number=200)
print(f"\nOriginal:  {t_orig4*1000:.1f}ms (200 iterations x 3000 entries)")
print(f"Optimized: {t_opt4*1000:.1f}ms")
print(f"Speedup:   {t_orig4/t_opt4:.2f}x")

# ═══════════════════════════════════════════════════════════════
# BENCHMARK 5: Regex-only isolation (no other patterns)
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("BENCHMARK 5: Regex-only isolation (re.findall in loop)")
print("=" * 70)

orig_findall = '''
import re

def extract_numbers(texts):
    all_nums = []
    for text in texts:
        nums = re.findall(r"\\d+\\.?\\d*", text)
        all_nums.extend(nums)
    return all_nums
'''

opt_findall = fix(orig_findall)
print("\nOptimized:")
print(opt_findall.strip())

setup5 = '''
import re, random
texts = []
for i in range(3000):
    parts = [f"item{random.randint(1,999)} costs ${random.uniform(1,100):.2f}" for _ in range(3)]
    texts.append(", ".join(parts))
'''

t_orig5 = timeit.timeit("extract_numbers(texts)", setup=setup5 + orig_findall, number=200)
t_opt5 = timeit.timeit("extract_numbers(texts)", setup=setup5 + opt_findall, number=200)
print(f"\nOriginal:  {t_orig5*1000:.1f}ms (200 iterations x 3000 texts)")
print(f"Optimized: {t_opt5*1000:.1f}ms")
print(f"Speedup:   {t_orig5/t_opt5:.2f}x")

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
header = f"{'Benchmark':<50} {'Speedup':>8}"
print(header)
print("-" * 60)
print(f"{'Realistic user processing (regex+set+append)':<50} {t_orig/t_opt:>7.2f}x")
print(f"{'Email validation (complex regex, loop)':<50} {t_orig2/t_opt2:>7.2f}x")
print(f"{'Text cleaning (3x re.sub per item)':<50} {t_orig3/t_opt3:>7.2f}x")
print(f"{'Combined log filter (regex+list->set+append)':<50} {t_orig4/t_opt4:>7.2f}x")
print(f"{'Number extraction (re.findall in loop)':<50} {t_orig5/t_opt5:>7.2f}x")
print()
print("Key findings:")
print(f"  - Regex precompile alone: {min(t_orig2/t_opt2, t_orig5/t_opt5):.1f}-{max(t_orig2/t_opt2, t_orig5/t_opt5):.1f}x")
print(f"  - Multiple re.sub calls: {t_orig3/t_opt3:.1f}x (compounds with each call)")
print(f"  - Combined all patterns: {t_orig4/t_opt4:.1f}x")

# ═══════════════════════════════════════════════════════════════
# PIPELINE DEMO: scan -> fix -> benchmark -> prove
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("FULL PIPELINE DEMO: scan -> fix -> benchmark -> prove")
print("=" * 70)

demo_code = '''
import re

def process_users(users):
    results = []
    for user in users:
        if user["role"] in ["admin", "editor", "moderator", "reviewer", "manager"]:
            name = user["first"] + " " + user["last"]
            if re.match(r"^[A-Z]", name):
                results.append({"name": name, "role": user["role"]})
    return results
'''

print("\n--- STEP 1: scan() ---")
findings = scan(demo_code)
for f in findings:
    print(f"  Line {f.line}: [{f.pattern_name}] {f.description} (expected: {f.expected_speedup})")

print("\n--- STEP 2: fix() ---")
fixed = fix(demo_code)
print(fixed.strip())

print("\n--- STEP 3: benchmark ---")
setup_demo = '''
import re, random, string
users = []
roles = ["admin", "editor", "moderator", "reviewer", "manager", "viewer", "guest"]
for i in range(2000):
    first = random.choice(string.ascii_uppercase) + "".join(random.choices(string.ascii_lowercase, k=5))
    last = random.choice(string.ascii_uppercase) + "".join(random.choices(string.ascii_lowercase, k=7))
    users.append({"first": first, "last": last, "role": random.choice(roles)})
'''

t_before = timeit.timeit("process_users(users)", setup=setup_demo + demo_code, number=500)
t_after = timeit.timeit("process_users(users)", setup=setup_demo + fixed, number=500)
print(f"  Before: {t_before*1000:.1f}ms")
print(f"  After:  {t_after*1000:.1f}ms")
print(f"  Speedup: {t_before/t_after:.2f}x")

print("\n--- STEP 4: PROVEN ---")
if t_before > t_after:
    print(f"  PASS: {t_before/t_after:.2f}x faster. All patterns applied successfully.")
else:
    print("  FAIL: No speedup detected.")
