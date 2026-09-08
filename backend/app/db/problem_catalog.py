"""The curated catalog of 50 DSA problems shipped with CodeForge AI.

Every problem is judged from stdin/stdout so the same test data works for all
five supported languages. Each spec carries a Python ``reference_solution``;
``tests/test_problem_catalog.py`` executes it against every test case, which is
what keeps the seeded expected outputs honest.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core import languages


@dataclass(frozen=True)
class ProblemSpec:
    """One seedable problem plus the reference solution that validates it."""

    slug: str
    title: str
    difficulty: str
    category: str
    summary: str
    input_description: str
    output_description: str
    constraints: list[str]
    cases: list[tuple[str, str]]
    """``(stdin, expected_stdout)``. The first two double as public samples."""
    reference_solution: str
    editorial: str = ""
    sample_count: int = field(default=2)

    @property
    def description_md(self) -> str:
        example_block = "\n\n".join(
            f"**Example {index}**\n\n```\nInput:\n{stdin.strip()}\n\nOutput:\n{expected.strip()}\n```"
            for index, (stdin, expected) in enumerate(self.cases[: self.sample_count], start=1)
        )
        return (
            f"{self.summary}\n\n"
            f"## Input\n\n{self.input_description}\n\n"
            f"## Output\n\n{self.output_description}\n\n"
            f"## Examples\n\n{example_block}\n"
        )

    @property
    def starter_code(self) -> dict[str, str]:
        return languages.starter_code_for_all(
            [
                f"{self.title}",
                "",
                "Input:",
                *self.input_description.splitlines(),
                "",
                "Output:",
                *self.output_description.splitlines(),
            ]
        )

    @property
    def supported_languages(self) -> list[str]:
        return list(languages.LANGUAGE_IDS)


P = ProblemSpec

CATALOG: list[ProblemSpec] = [
    # ---------------------------------------------------------------- arrays
    P(
        slug="array-sum",
        title="Array Sum",
        difficulty="easy",
        category="arrays",
        summary="Warm up by adding every integer in an array.",
        input_description="Line 1: n, the number of integers.\nLine 2: n space-separated integers.",
        output_description="A single integer: the sum of all n values.",
        constraints=["1 <= n <= 100000", "-10^9 <= value <= 10^9"],
        cases=[
            ("3\n1 2 3\n", "6\n"),
            ("1\n-5\n", "-5\n"),
            ("5\n10 20 30 40 50\n", "150\n"),
            ("4\n0 0 0 0\n", "0\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
print(sum(data[1:1 + n]))
""",
        editorial="A single linear pass accumulates the total in O(n) time and O(1) space.",
    ),
    P(
        slug="two-sum",
        title="Two Sum",
        difficulty="easy",
        category="arrays",
        summary=(
            "Given an array of integers and a target, find the two entries that add up to the "
            "target. Exactly one valid answer exists."
        ),
        input_description=(
            "Line 1: n and target, space-separated.\nLine 2: n space-separated integers."
        ),
        output_description=(
            "Two space-separated 0-based indices, smaller index first, of the pair that sums "
            "to target."
        ),
        constraints=["2 <= n <= 10000", "Exactly one valid pair exists."],
        cases=[
            ("4 9\n2 7 11 15\n", "0 1\n"),
            ("3 6\n3 2 4\n", "1 2\n"),
            ("2 6\n3 3\n", "0 1\n"),
            ("5 10\n1 2 3 4 6\n", "3 4\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n, target = data[0], data[1]
nums = data[2:2 + n]
seen = {}
for index, value in enumerate(nums):
    if target - value in seen:
        print(seen[target - value], index)
        break
    seen[value] = index
""",
        editorial=(
            "Store each visited value's index in a hash map and look up `target - value` as you "
            "scan. That replaces the O(n^2) nested loop with a single O(n) pass."
        ),
    ),
    P(
        slug="best-time-stock",
        title="Best Time to Buy and Sell Stock",
        difficulty="easy",
        category="arrays",
        summary=(
            "Given daily prices, pick one day to buy and a later day to sell to maximise profit."
        ),
        input_description="Line 1: n.\nLine 2: n space-separated prices.",
        output_description="The maximum achievable profit, or 0 if no profitable trade exists.",
        constraints=["1 <= n <= 100000", "0 <= price <= 10^5"],
        cases=[
            ("6\n7 1 5 3 6 4\n", "5\n"),
            ("5\n7 6 4 3 1\n", "0\n"),
            ("2\n1 2\n", "1\n"),
            ("1\n5\n", "0\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
prices = data[1:1 + n]
best = 0
cheapest = prices[0]
for price in prices[1:]:
    best = max(best, price - cheapest)
    cheapest = min(cheapest, price)
print(best)
""",
        editorial=(
            "Track the cheapest price seen so far; the answer is the largest difference between "
            "the current price and that running minimum."
        ),
    ),
    P(
        slug="contains-duplicate",
        title="Contains Duplicate",
        difficulty="easy",
        category="arrays",
        summary="Decide whether any value appears at least twice in the array.",
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description="`true` if any value repeats, otherwise `false`.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("4\n1 2 3 1\n", "true\n"),
            ("4\n1 2 3 4\n", "false\n"),
            ("1\n1\n", "false\n"),
            ("10\n1 1 1 3 3 4 3 2 4 2\n", "true\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = data[1:1 + n]
print("true" if len(set(nums)) < n else "false")
""",
        editorial="Insert into a hash set; a duplicate is detected the moment the set stops growing.",
    ),
    P(
        slug="majority-element",
        title="Majority Element",
        difficulty="easy",
        category="arrays",
        summary=("Find the value that appears more than n/2 times. It is guaranteed to exist."),
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description="The majority value.",
        constraints=["1 <= n <= 100000", "A majority element always exists."],
        cases=[
            ("3\n3 2 3\n", "3\n"),
            ("7\n2 2 1 1 1 2 2\n", "2\n"),
            ("1\n9\n", "9\n"),
            ("5\n6 6 6 1 2\n", "6\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = data[1:1 + n]
candidate = None
count = 0
for value in nums:
    if count == 0:
        candidate = value
    count += 1 if value == candidate else -1
print(candidate)
""",
        editorial=(
            "Boyer-Moore voting keeps one candidate and a counter, solving it in O(n) time and "
            "O(1) space without sorting."
        ),
    ),
    P(
        slug="single-number",
        title="Single Number",
        difficulty="easy",
        category="bit manipulation",
        summary=("Every value appears exactly twice except one. Find the value that appears once."),
        input_description="Line 1: n (always odd).\nLine 2: n space-separated integers.",
        output_description="The value that appears exactly once.",
        constraints=["1 <= n <= 100000", "Every other value appears exactly twice."],
        cases=[
            ("3\n2 2 1\n", "1\n"),
            ("5\n4 1 2 1 2\n", "4\n"),
            ("1\n7\n", "7\n"),
            ("7\n5 3 5 9 3 9 8\n", "8\n"),
        ],
        reference_solution="""import sys
from functools import reduce
data = list(map(int, sys.stdin.read().split()))
n = data[0]
print(reduce(lambda a, b: a ^ b, data[1:1 + n]))
""",
        editorial=(
            "XOR is associative and self-cancelling, so XOR-ing the whole array leaves only the "
            "unpaired value. O(n) time, O(1) space."
        ),
    ),
    P(
        slug="move-zeroes",
        title="Move Zeroes",
        difficulty="easy",
        category="two pointers",
        summary=(
            "Shift every zero to the end of the array while keeping the relative order of the "
            "non-zero values."
        ),
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description="The n rearranged values, space-separated on one line.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("5\n0 1 0 3 12\n", "1 3 12 0 0\n"),
            ("1\n0\n", "0\n"),
            ("4\n0 0 1 2\n", "1 2 0 0\n"),
            ("3\n1 2 3\n", "1 2 3\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = data[1:1 + n]
kept = [value for value in nums if value != 0]
print(*(kept + [0] * (n - len(kept))))
""",
        editorial=(
            "A write pointer copies each non-zero forward, then the tail is filled with zeroes."
        ),
    ),
    P(
        slug="product-except-self",
        title="Product of Array Except Self",
        difficulty="medium",
        category="arrays",
        summary=(
            "For each position print the product of every other element. Solve it without "
            "division."
        ),
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description="n space-separated products on one line.",
        constraints=["2 <= n <= 100000", "The full product fits in a 64-bit integer."],
        cases=[
            ("4\n1 2 3 4\n", "24 12 8 6\n"),
            ("4\n-1 1 0 -3\n", "0 0 3 0\n"),
            ("2\n2 3\n", "3 2\n"),
            ("3\n1 1 1\n", "1 1 1\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = data[1:1 + n]
result = [1] * n
prefix = 1
for i in range(n):
    result[i] = prefix
    prefix *= nums[i]
suffix = 1
for i in range(n - 1, -1, -1):
    result[i] *= suffix
    suffix *= nums[i]
print(*result)
""",
        editorial=(
            "Two sweeps: one accumulating the running prefix product, one the suffix product. "
            "Multiplying them gives every answer in O(n) without division."
        ),
    ),
    P(
        slug="rotate-array",
        title="Rotate Array",
        difficulty="medium",
        category="arrays",
        summary="Rotate the array to the right by k positions.",
        input_description="Line 1: n and k.\nLine 2: n space-separated integers.",
        output_description="The rotated array, space-separated on one line.",
        constraints=["1 <= n <= 100000", "0 <= k <= 10^9"],
        cases=[
            ("7 3\n1 2 3 4 5 6 7\n", "5 6 7 1 2 3 4\n"),
            ("4 2\n-1 -100 3 99\n", "3 99 -1 -100\n"),
            ("1 0\n5\n", "5\n"),
            ("3 4\n1 2 3\n", "3 1 2\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n, k = data[0], data[1] % data[0]
nums = data[2:2 + n]
print(*(nums[-k:] + nums[:-k] if k else nums))
""",
        editorial=(
            "Reduce k modulo n, then the answer is the last k elements followed by the rest. "
            "The in-place variant reverses three ranges."
        ),
    ),
    P(
        slug="maximum-subarray",
        title="Maximum Subarray",
        difficulty="medium",
        category="dynamic programming",
        summary="Find the largest sum obtainable from a contiguous, non-empty subarray.",
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description="The maximum contiguous subarray sum.",
        constraints=["1 <= n <= 100000", "-10^4 <= value <= 10^4"],
        cases=[
            ("9\n-2 1 -3 4 -1 2 1 -5 4\n", "6\n"),
            ("1\n1\n", "1\n"),
            ("3\n-3 -2 -1\n", "-1\n"),
            ("4\n5 4 -1 7\n", "15\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = data[1:1 + n]
best = current = nums[0]
for value in nums[1:]:
    current = max(value, current + value)
    best = max(best, current)
print(best)
""",
        editorial=(
            "Kadane's algorithm: at each index either extend the previous subarray or restart "
            "from the current value, keeping the best total seen."
        ),
    ),
    P(
        slug="trapping-rain-water",
        title="Trapping Rain Water",
        difficulty="hard",
        category="two pointers",
        summary=(
            "Given an elevation map of unit-width bars, compute how much rain water is trapped."
        ),
        input_description="Line 1: n.\nLine 2: n space-separated non-negative heights.",
        output_description="The total units of trapped water.",
        constraints=["1 <= n <= 100000", "0 <= height <= 10^5"],
        cases=[
            ("12\n0 1 0 2 1 0 1 3 2 1 2 1\n", "6\n"),
            ("6\n4 2 0 3 2 5\n", "9\n"),
            ("3\n1 2 3\n", "0\n"),
            ("1\n5\n", "0\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
height = data[1:1 + n]
left, right = 0, n - 1
left_max = right_max = total = 0
while left < right:
    if height[left] < height[right]:
        left_max = max(left_max, height[left])
        total += left_max - height[left]
        left += 1
    else:
        right_max = max(right_max, height[right])
        total += right_max - height[right]
        right -= 1
print(total)
""",
        editorial=(
            "Two pointers walk inward from both ends. The shorter side always bounds the water "
            "level there, so its running maximum determines the trapped depth in O(n)/O(1)."
        ),
    ),
    P(
        slug="container-most-water",
        title="Container With Most Water",
        difficulty="medium",
        category="two pointers",
        summary=(
            "Pick two lines that together with the x-axis form the container holding the most "
            "water."
        ),
        input_description="Line 1: n.\nLine 2: n space-separated heights.",
        output_description="The maximum area that can be contained.",
        constraints=["2 <= n <= 100000", "0 <= height <= 10^4"],
        cases=[
            ("9\n1 8 6 2 5 4 8 3 7\n", "49\n"),
            ("2\n1 1\n", "1\n"),
            ("3\n4 3 2\n", "4\n"),
            ("5\n1 2 1 3 2\n", "6\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
height = data[1:1 + n]
left, right = 0, n - 1
best = 0
while left < right:
    best = max(best, (right - left) * min(height[left], height[right]))
    if height[left] < height[right]:
        left += 1
    else:
        right -= 1
print(best)
""",
        editorial=(
            "Start at the widest pair and move the shorter line inward; any pair skipped that way "
            "is strictly narrower and no taller, so it cannot beat the current best."
        ),
    ),
    P(
        slug="3sum",
        title="3Sum",
        difficulty="medium",
        category="two pointers",
        summary="List every unique triplet of values that sums to zero.",
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description=(
            "One triplet per line, each printed in ascending order, with the lines themselves in "
            "ascending order. Print nothing when no triplet exists."
        ),
        constraints=["1 <= n <= 3000", "Triplets must be unique by value."],
        cases=[
            ("6\n-1 0 1 2 -1 -4\n", "-1 -1 2\n-1 0 1\n"),
            ("3\n0 1 1\n", "\n"),
            ("3\n0 0 0\n", "0 0 0\n"),
            ("4\n-2 0 1 1\n", "-2 1 1\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = sorted(data[1:1 + n])
for i in range(n - 2):
    if i and nums[i] == nums[i - 1]:
        continue
    lo, hi = i + 1, n - 1
    while lo < hi:
        total = nums[i] + nums[lo] + nums[hi]
        if total < 0:
            lo += 1
        elif total > 0:
            hi -= 1
        else:
            print(nums[i], nums[lo], nums[hi])
            lo += 1
            while lo < hi and nums[lo] == nums[lo - 1]:
                lo += 1
            hi -= 1
""",
        editorial=(
            "Sort, then fix the first value and two-pointer the remaining suffix. Skipping equal "
            "neighbours removes duplicates without a set. O(n^2)."
        ),
    ),
    # --------------------------------------------------------------- strings
    P(
        slug="palindrome-string",
        title="Palindrome String",
        difficulty="easy",
        category="strings",
        summary="Decide whether a word reads the same forwards and backwards.",
        input_description="A single line containing one word with no spaces.",
        output_description="`true` if the word is a palindrome, otherwise `false`.",
        constraints=["1 <= length <= 100000"],
        cases=[
            ("level\n", "true\n"),
            ("code\n", "false\n"),
            ("a\n", "true\n"),
            ("racecar\n", "true\n"),
        ],
        reference_solution="""import sys
s = sys.stdin.read().strip()
print("true" if s == s[::-1] else "false")
""",
        editorial="Compare characters from both ends inward, or simply against the reversal.",
    ),
    P(
        slug="valid-anagram",
        title="Valid Anagram",
        difficulty="easy",
        category="strings",
        summary="Decide whether the second word is a rearrangement of the first.",
        input_description="A single line with two space-separated words, s and t.",
        output_description="`true` if t is an anagram of s, otherwise `false`.",
        constraints=["1 <= length <= 100000", "Words contain lowercase letters only."],
        cases=[
            ("anagram nagaram\n", "true\n"),
            ("rat car\n", "false\n"),
            ("a a\n", "true\n"),
            ("listen silent\n", "true\n"),
        ],
        reference_solution="""import sys
from collections import Counter
s, t = sys.stdin.read().split()
print("true" if Counter(s) == Counter(t) else "false")
""",
        editorial=(
            "Counting characters is O(n); sorting both strings also works but costs O(n log n)."
        ),
    ),
    P(
        slug="longest-common-prefix",
        title="Longest Common Prefix",
        difficulty="easy",
        category="strings",
        summary="Find the longest string that prefixes every word in the list.",
        input_description="A single line of space-separated lowercase words.",
        output_description=(
            'The longest common prefix, or the two characters `""` when there is no common '
            "prefix."
        ),
        constraints=["1 <= number of words <= 200", "1 <= word length <= 200"],
        cases=[
            ("flower flow flight\n", "fl\n"),
            ("dog racecar car\n", '""\n'),
            ("interspecies interstellar interstate\n", "inters\n"),
            ("abc\n", "abc\n"),
        ],
        reference_solution="""import sys
words = sys.stdin.read().split()
prefix = words[0]
for word in words[1:]:
    while not word.startswith(prefix):
        prefix = prefix[:-1]
        if not prefix:
            break
print(prefix if prefix else '""')
""",
        editorial=(
            "Hold a candidate prefix and shrink it until it prefixes each word in turn. "
            "Worst case O(total characters)."
        ),
    ),
    P(
        slug="reverse-words",
        title="Reverse Words in a String",
        difficulty="easy",
        category="strings",
        summary=("Reverse the order of the words in a sentence, collapsing any extra whitespace."),
        input_description="A single line containing words separated by one or more spaces.",
        output_description="The words in reverse order, separated by exactly one space.",
        constraints=["1 <= line length <= 10000", "At least one word is present."],
        cases=[
            ("the sky is blue\n", "blue is sky the\n"),
            ("  hello world  \n", "world hello\n"),
            ("a good   example\n", "example good a\n"),
            ("single\n", "single\n"),
        ],
        reference_solution="""import sys
print(*reversed(sys.stdin.read().split()))
""",
        editorial=(
            "Splitting on runs of whitespace discards the padding for free; then emit the tokens "
            "in reverse."
        ),
    ),
    P(
        slug="first-unique-character",
        title="First Unique Character",
        difficulty="easy",
        category="hashing",
        summary="Find the first character in a string that never repeats.",
        input_description="A single line containing one lowercase word.",
        output_description="The 0-based index of the first non-repeating character, or -1.",
        constraints=["1 <= length <= 100000"],
        cases=[
            ("leetcode\n", "0\n"),
            ("aabb\n", "-1\n"),
            ("loveleetcode\n", "2\n"),
            ("z\n", "0\n"),
        ],
        reference_solution="""import sys
from collections import Counter
s = sys.stdin.read().strip()
counts = Counter(s)
for index, char in enumerate(s):
    if counts[char] == 1:
        print(index)
        break
else:
    print(-1)
""",
        editorial=(
            "One pass builds the frequency table, a second pass returns the first character whose "
            "count is 1."
        ),
    ),
    P(
        slug="group-anagrams-count",
        title="Group Anagrams Count",
        difficulty="medium",
        category="hashing",
        summary="Count how many distinct anagram groups a list of words falls into.",
        input_description="A single line of space-separated lowercase words.",
        output_description="The number of anagram groups.",
        constraints=["1 <= number of words <= 10000"],
        cases=[
            ("eat tea tan ate nat bat\n", "3\n"),
            ("a\n", "1\n"),
            ("ab ba\n", "1\n"),
            ("a b c\n", "3\n"),
        ],
        reference_solution="""import sys
words = sys.stdin.read().split()
print(len({"".join(sorted(word)) for word in words}))
""",
        editorial=(
            "The sorted letters of a word are a canonical key shared by all its anagrams, so the "
            "answer is the number of distinct keys."
        ),
    ),
    P(
        slug="longest-unique-substring",
        title="Longest Substring Without Repeating Characters",
        difficulty="medium",
        category="sliding window",
        summary="Find the length of the longest substring containing no repeated character.",
        input_description="A single line containing the string (it may be empty).",
        output_description="The length of the longest substring with all-distinct characters.",
        constraints=["0 <= length <= 100000"],
        cases=[
            ("abcabcbb\n", "3\n"),
            ("bbbbb\n", "1\n"),
            ("pwwkew\n", "3\n"),
            ("\n", "0\n"),
        ],
        reference_solution="""import sys
s = sys.stdin.read().strip()
last_seen = {}
best = start = 0
for index, char in enumerate(s):
    if char in last_seen and last_seen[char] >= start:
        start = last_seen[char] + 1
    last_seen[char] = index
    best = max(best, index - start + 1)
print(best)
""",
        editorial=(
            "Slide a window and remember each character's last index. On a repeat, jump the left "
            "edge past the previous occurrence. O(n)."
        ),
    ),
    P(
        slug="minimum-window-length",
        title="Minimum Window Substring Length",
        difficulty="hard",
        category="sliding window",
        summary=(
            "Find the shortest substring of s that contains every character of t, counting "
            "duplicates."
        ),
        input_description="A single line with two space-separated words, s and t.",
        output_description="The length of the shortest valid window, or -1 if none exists.",
        constraints=["1 <= length of s, t <= 100000"],
        cases=[
            ("ADOBECODEBANC ABC\n", "4\n"),
            ("a aa\n", "-1\n"),
            ("a a\n", "1\n"),
            ("ab b\n", "1\n"),
        ],
        reference_solution="""import sys
from collections import Counter
s, t = sys.stdin.read().split()
need = Counter(t)
missing = len(t)
best = len(s) + 1
left = 0
for right, char in enumerate(s):
    if need[char] > 0:
        missing -= 1
    need[char] -= 1
    while missing == 0:
        best = min(best, right - left + 1)
        need[s[left]] += 1
        if need[s[left]] > 0:
            missing += 1
        left += 1
print(best if best <= len(s) else -1)
""",
        editorial=(
            "Expand the right edge until every required character is covered, then contract the "
            "left edge while it stays valid. Each index moves at most twice, so O(n)."
        ),
    ),
    P(
        slug="edit-distance",
        title="Edit Distance",
        difficulty="hard",
        category="dynamic programming",
        summary=(
            "Compute the minimum number of insertions, deletions or substitutions that turn the "
            "first word into the second."
        ),
        input_description="A single line with two space-separated words.",
        output_description="The minimum number of edit operations.",
        constraints=["1 <= word length <= 500"],
        cases=[
            ("horse ros\n", "3\n"),
            ("intention execution\n", "5\n"),
            ("abc abc\n", "0\n"),
            ("a ab\n", "1\n"),
        ],
        reference_solution="""import sys
a, b = sys.stdin.read().split()
previous = list(range(len(b) + 1))
for i, char_a in enumerate(a, start=1):
    current = [i]
    for j, char_b in enumerate(b, start=1):
        if char_a == char_b:
            current.append(previous[j - 1])
        else:
            current.append(1 + min(previous[j - 1], previous[j], current[j - 1]))
    previous = current
print(previous[-1])
""",
        editorial=(
            "Classic Levenshtein DP over a table of prefix pairs; only the previous row is needed, "
            "so memory drops to O(len(b))."
        ),
    ),
    P(
        slug="word-break",
        title="Word Break",
        difficulty="medium",
        category="dynamic programming",
        summary=(
            "Decide whether a string can be segmented into a sequence of dictionary words. "
            "Words may be reused."
        ),
        input_description="Line 1: the string s.\nLine 2: space-separated dictionary words.",
        output_description="`true` if s can be segmented, otherwise `false`.",
        constraints=["1 <= length of s <= 300", "1 <= dictionary size <= 1000"],
        cases=[
            ("leetcode\nleet code\n", "true\n"),
            ("applepenapple\napple pen\n", "true\n"),
            ("catsandog\ncats dog sand and cat\n", "false\n"),
            ("aaaab\na aa aaa\n", "false\n"),
        ],
        reference_solution="""import sys
lines = sys.stdin.read().splitlines()
s = lines[0].strip()
words = set(lines[1].split())
reachable = [True] + [False] * len(s)
for end in range(1, len(s) + 1):
    for start in range(end):
        if reachable[start] and s[start:end] in words:
            reachable[end] = True
            break
print("true" if reachable[len(s)] else "false")
""",
        editorial=(
            "`reachable[i]` marks that the first i characters are segmentable. Extend it by "
            "testing every suffix ending at i against the dictionary. O(n^2) substring checks."
        ),
    ),
    # ----------------------------------------------------- stacks and queues
    P(
        slug="valid-parentheses",
        title="Valid Parentheses",
        difficulty="easy",
        category="stack",
        summary="Decide whether a bracket string is balanced and correctly nested.",
        input_description="A single line containing only the characters ()[]{}.",
        output_description="`true` if the brackets are valid, otherwise `false`.",
        constraints=["1 <= length <= 100000"],
        cases=[
            ("()[]{}\n", "true\n"),
            ("(]\n", "false\n"),
            ("{[]}\n", "true\n"),
            ("((\n", "false\n"),
        ],
        reference_solution="""import sys
s = sys.stdin.read().strip()
pairs = {")": "(", "]": "[", "}": "{"}
stack = []
ok = True
for char in s:
    if char in pairs:
        if not stack or stack.pop() != pairs[char]:
            ok = False
            break
    else:
        stack.append(char)
print("true" if ok and not stack else "false")
""",
        editorial=(
            "Push opening brackets and require each closing bracket to match the top of the "
            "stack. A leftover stack means unclosed brackets."
        ),
    ),
    P(
        slug="daily-temperatures",
        title="Daily Temperatures",
        difficulty="medium",
        category="stack",
        summary=(
            "For each day, report how many days you must wait for a strictly warmer temperature."
        ),
        input_description="Line 1: n.\nLine 2: n space-separated temperatures.",
        output_description="n space-separated waits; 0 when no warmer day follows.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("8\n73 74 75 71 69 72 76 73\n", "1 1 4 2 1 1 0 0\n"),
            ("1\n30\n", "0\n"),
            ("3\n30 40 50\n", "1 1 0\n"),
            ("3\n50 40 30\n", "0 0 0\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
temps = data[1:1 + n]
answer = [0] * n
stack = []
for index, temp in enumerate(temps):
    while stack and temps[stack[-1]] < temp:
        previous = stack.pop()
        answer[previous] = index - previous
    stack.append(index)
print(*answer)
""",
        editorial=(
            "A monotonically decreasing stack of indices: each new temperature resolves every "
            "colder day still waiting. Each index is pushed and popped once, so O(n)."
        ),
    ),
    P(
        slug="implement-queue",
        title="Queue Front",
        difficulty="easy",
        category="queue",
        summary="Enqueue every value in order and report the element at the front.",
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description="The value at the front of the queue.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("3\n4 5 6\n", "4\n"),
            ("1\n9\n", "9\n"),
            ("2\n-1 1\n", "-1\n"),
            ("4\n0 3 2 1\n", "0\n"),
        ],
        reference_solution="""import sys
from collections import deque
data = list(map(int, sys.stdin.read().split()))
queue = deque(data[1:1 + data[0]])
print(queue[0])
""",
        editorial="A FIFO queue preserves insertion order, so the front is the first value read.",
    ),
    P(
        slug="lru-cache",
        title="LRU Cache Eviction",
        difficulty="medium",
        category="design",
        summary=(
            "Simulate a fixed-capacity LRU cache. `put` inserts or updates and `get` reads, both "
            "marking the key as most recently used. Inserting beyond capacity evicts the least "
            "recently used key."
        ),
        input_description=(
            "Line 1: the capacity.\nEach following line is either `put <key> <value>` or "
            "`get <key>`."
        ),
        output_description=(
            "The results of every `get`, in order, space-separated on one line. A miss prints -1."
        ),
        constraints=["1 <= capacity <= 10000", "1 <= number of operations <= 100000"],
        cases=[
            ("2\nput 1 1\nput 2 2\nget 1\nput 3 3\nget 2\n", "1 -1\n"),
            ("1\nput 2 1\nget 2\nput 3 2\nget 2\n", "1 -1\n"),
            ("2\nget 2\nput 2 6\nget 1\nput 1 5\nget 1\nget 2\n", "-1 -1 5 6\n"),
            ("3\nput 1 10\nput 2 20\nput 3 30\nget 1\nget 2\nget 3\n", "10 20 30\n"),
        ],
        reference_solution="""import sys
from collections import OrderedDict
lines = sys.stdin.read().splitlines()
capacity = int(lines[0])
cache = OrderedDict()
results = []
for line in lines[1:]:
    parts = line.split()
    if not parts:
        continue
    if parts[0] == "put":
        key, value = int(parts[1]), int(parts[2])
        if key in cache:
            cache.move_to_end(key)
        cache[key] = value
        if len(cache) > capacity:
            cache.popitem(last=False)
    else:
        key = int(parts[1])
        if key in cache:
            cache.move_to_end(key)
            results.append(cache[key])
        else:
            results.append(-1)
print(*results)
""",
        editorial=(
            "A hash map plus a doubly linked list gives O(1) `get` and `put`; Python's "
            "`OrderedDict` provides exactly that with `move_to_end` and `popitem`."
        ),
    ),
    # ---------------------------------------------------------- linked lists
    P(
        slug="reverse-linked-list",
        title="Reverse Linked List",
        difficulty="easy",
        category="linked list",
        summary="Reverse a singly linked list and print the resulting order.",
        input_description="Line 1: n.\nLine 2: the n node values in list order.",
        output_description="The n values in reversed order, space-separated.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("5\n1 2 3 4 5\n", "5 4 3 2 1\n"),
            ("2\n1 2\n", "2 1\n"),
            ("1\n1\n", "1\n"),
            ("3\n10 20 30\n", "30 20 10\n"),
        ],
        reference_solution="""import sys
data = sys.stdin.read().split()
n = int(data[0])
print(*reversed(data[1:1 + n]))
""",
        editorial=(
            "Walk the list re-pointing each `next` to the previously visited node, keeping three "
            "pointers. O(n) time, O(1) extra space."
        ),
    ),
    P(
        slug="middle-linked-list",
        title="Middle of the Linked List",
        difficulty="easy",
        category="linked list",
        summary="Report the middle node's value; with an even length, take the second middle.",
        input_description="Line 1: n.\nLine 2: the n node values in list order.",
        output_description="The value stored in the middle node.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("5\n1 2 3 4 5\n", "3\n"),
            ("4\n1 2 3 4\n", "3\n"),
            ("1\n7\n", "7\n"),
            ("2\n8 9\n", "9\n"),
        ],
        reference_solution="""import sys
data = sys.stdin.read().split()
n = int(data[0])
print(data[1:1 + n][n // 2])
""",
        editorial=(
            "Advance a slow pointer one step and a fast pointer two steps; when fast runs off the "
            "end, slow sits on the middle."
        ),
    ),
    # -------------------------------------------------------- binary  search
    P(
        slug="binary-search",
        title="Binary Search",
        difficulty="easy",
        category="binary search",
        summary="Locate a target in a sorted array in logarithmic time.",
        input_description=(
            "Line 1: n and target.\nLine 2: n space-separated integers in ascending order."
        ),
        output_description="The 0-based index of target, or -1 if it is absent.",
        constraints=["1 <= n <= 100000", "The array is sorted ascending with distinct values."],
        cases=[
            ("5 9\n-1 0 3 5 9\n", "4\n"),
            ("4 2\n1 3 5 7\n", "-1\n"),
            ("1 4\n4\n", "0\n"),
            ("3 1\n1 2 3\n", "0\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n, target = data[0], data[1]
nums = data[2:2 + n]
lo, hi = 0, n - 1
found = -1
while lo <= hi:
    mid = (lo + hi) // 2
    if nums[mid] == target:
        found = mid
        break
    if nums[mid] < target:
        lo = mid + 1
    else:
        hi = mid - 1
print(found)
""",
        editorial="Halve the search range each step by comparing against the midpoint. O(log n).",
    ),
    P(
        slug="search-rotated-array",
        title="Search in Rotated Sorted Array",
        difficulty="medium",
        category="binary search",
        summary=(
            "A sorted array with distinct values was rotated at an unknown pivot. Find the "
            "target in logarithmic time."
        ),
        input_description="Line 1: n and target.\nLine 2: the n rotated values.",
        output_description="The 0-based index of target, or -1 if it is absent.",
        constraints=["1 <= n <= 100000", "All values are distinct."],
        cases=[
            ("7 0\n4 5 6 7 0 1 2\n", "4\n"),
            ("7 3\n4 5 6 7 0 1 2\n", "-1\n"),
            ("1 0\n1\n", "-1\n"),
            ("2 1\n3 1\n", "1\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n, target = data[0], data[1]
nums = data[2:2 + n]
lo, hi = 0, n - 1
found = -1
while lo <= hi:
    mid = (lo + hi) // 2
    if nums[mid] == target:
        found = mid
        break
    if nums[lo] <= nums[mid]:
        if nums[lo] <= target < nums[mid]:
            hi = mid - 1
        else:
            lo = mid + 1
    else:
        if nums[mid] < target <= nums[hi]:
            lo = mid + 1
        else:
            hi = mid - 1
print(found)
""",
        editorial=(
            "At every midpoint one half is guaranteed sorted. Test whether the target lies inside "
            "that sorted half and discard the other half."
        ),
    ),
    P(
        slug="find-minimum-rotated",
        title="Find Minimum in Rotated Sorted Array",
        difficulty="medium",
        category="binary search",
        summary="Find the smallest value in a rotated sorted array of distinct integers.",
        input_description="Line 1: n.\nLine 2: the n rotated values.",
        output_description="The minimum value.",
        constraints=["1 <= n <= 100000", "All values are distinct."],
        cases=[
            ("5\n3 4 5 1 2\n", "1\n"),
            ("7\n4 5 6 7 0 1 2\n", "0\n"),
            ("1\n1\n", "1\n"),
            ("3\n11 13 15\n", "11\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = data[1:1 + n]
lo, hi = 0, n - 1
while lo < hi:
    mid = (lo + hi) // 2
    if nums[mid] > nums[hi]:
        lo = mid + 1
    else:
        hi = mid
print(nums[lo])
""",
        editorial=(
            "Compare the midpoint with the right end: a larger midpoint means the pivot is to its "
            "right. The loop converges on the rotation point, which holds the minimum."
        ),
    ),
    P(
        slug="kth-largest",
        title="Kth Largest Element",
        difficulty="medium",
        category="heaps",
        summary="Find the kth largest value in an unsorted array (by order, not distinctness).",
        input_description="Line 1: n and k.\nLine 2: n space-separated integers.",
        output_description="The kth largest value.",
        constraints=["1 <= k <= n <= 100000"],
        cases=[
            ("6 2\n3 2 1 5 6 4\n", "5\n"),
            ("1 1\n7\n", "7\n"),
            ("4 4\n4 1 2 3\n", "1\n"),
            ("5 3\n9 9 8 7 6\n", "8\n"),
        ],
        reference_solution="""import sys
import heapq
data = list(map(int, sys.stdin.read().split()))
n, k = data[0], data[1]
print(heapq.nlargest(k, data[2:2 + n])[-1])
""",
        editorial=(
            "A size-k min-heap keeps the k largest values seen, giving O(n log k) — better than "
            "sorting when k is small."
        ),
    ),
    P(
        slug="top-k-frequent",
        title="Top K Frequent Elements",
        difficulty="medium",
        category="heaps",
        summary="Report the k values that occur most often.",
        input_description="Line 1: n and k.\nLine 2: n space-separated integers.",
        output_description=(
            "The k values on one line, ordered by descending frequency and, for ties, by "
            "ascending value."
        ),
        constraints=["1 <= k <= number of distinct values <= n <= 100000"],
        cases=[
            ("6 2\n1 1 1 2 2 3\n", "1 2\n"),
            ("1 1\n1\n", "1\n"),
            ("6 3\n4 4 5 5 6 7\n", "4 5 6\n"),
            ("5 1\n3 3 3 2 2\n", "3\n"),
        ],
        reference_solution="""import sys
from collections import Counter
data = list(map(int, sys.stdin.read().split()))
n, k = data[0], data[1]
counts = Counter(data[2:2 + n])
ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
print(*(value for value, _ in ranked[:k]))
""",
        editorial=(
            "Count with a hash map, then select the top k. Bucketing by frequency reaches O(n); "
            "a heap of size k reaches O(n log k)."
        ),
    ),
    P(
        slug="subarray-sum-equals-k",
        title="Subarray Sum Equals K",
        difficulty="medium",
        category="prefix sum",
        summary="Count the contiguous subarrays whose values sum to exactly k.",
        input_description="Line 1: n and k.\nLine 2: n space-separated integers (may be negative).",
        output_description="The number of qualifying subarrays.",
        constraints=["1 <= n <= 100000", "-10^7 <= k <= 10^7"],
        cases=[
            ("3 2\n1 1 1\n", "2\n"),
            ("4 3\n1 2 3 -3\n", "3\n"),
            ("1 0\n0\n", "1\n"),
            ("5 5\n5 0 0 -5 5\n", "5\n"),
        ],
        reference_solution="""import sys
from collections import defaultdict
data = list(map(int, sys.stdin.read().split()))
n, k = data[0], data[1]
nums = data[2:2 + n]
seen = defaultdict(int)
seen[0] = 1
running = 0
total = 0
for value in nums:
    running += value
    total += seen[running - k]
    seen[running] += 1
print(total)
""",
        editorial=(
            "A subarray sums to k exactly when two prefix sums differ by k. Count prefix sums in "
            "a hash map as you scan for an O(n) solution that tolerates negatives."
        ),
    ),
    # ----------------------------------------------------------------- trees
    P(
        slug="tree-max-depth",
        title="Maximum Depth of Binary Tree",
        difficulty="easy",
        category="trees",
        summary="Compute the number of nodes on the longest root-to-leaf path.",
        input_description=(
            "A single line holding the tree in LeetCode level-order bracket form, for example "
            "`[3,9,20,null,null,15,7]`. `[]` denotes an empty tree."
        ),
        output_description="The maximum depth.",
        constraints=["0 <= number of nodes <= 10000"],
        cases=[
            ("[3,9,20,null,null,15,7]\n", "3\n"),
            ("[]\n", "0\n"),
            ("[1]\n", "1\n"),
            ("[1,2,3,4]\n", "3\n"),
        ],
        reference_solution="""import sys
raw = sys.stdin.read().strip().strip("[]")
tokens = [token.strip() for token in raw.split(",") if token.strip()]
if not tokens:
    print(0)
else:
    depth = 0
    level = [0]
    cursor = 1
    while level:
        depth += 1
        next_level = []
        for _ in level:
            for _child in range(2):
                if cursor < len(tokens):
                    if tokens[cursor] != "null":
                        next_level.append(cursor)
                    cursor += 1
        level = next_level
    print(depth)
""",
        editorial=(
            "Level-order traversal counts levels directly; the recursive form is "
            "`1 + max(depth(left), depth(right))`."
        ),
    ),
    P(
        slug="lowest-common-ancestor",
        title="Lowest Common Ancestor in a BST",
        difficulty="medium",
        category="trees",
        summary=(
            "Build a binary search tree by inserting values in the given order, then find the "
            "lowest node that is an ancestor of both targets (a node may be its own ancestor)."
        ),
        input_description=(
            "Line 1: n, p and q.\nLine 2: the n distinct values in insertion order."
        ),
        output_description="The value of the lowest common ancestor of p and q.",
        constraints=["1 <= n <= 100000", "p and q are both present in the tree."],
        cases=[
            ("6 2 8\n6 2 8 0 4 7 9\n", "6\n"),
            ("3 2 3\n2 1 3\n", "2\n"),
            ("3 1 3\n2 1 3\n", "2\n"),
            ("1 5 5\n5\n", "5\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
p, q = data[1], data[2]
values = data[3:]
node = values[0]
while True:
    if p < node and q < node:
        candidates = [v for v in values if v < node]
    elif p > node and q > node:
        candidates = [v for v in values if v > node]
    else:
        break
    values = candidates
    node = values[0]
    index += 1
print(node)
""",
        editorial=(
            "In a BST, walk down from the root: if both targets are smaller go left, if both are "
            "larger go right. The first node that splits them is the LCA. O(height)."
        ),
    ),
    # ---------------------------------------------------------------- graphs
    P(
        slug="number-of-islands",
        title="Number of Islands",
        difficulty="medium",
        category="graphs",
        summary=(
            "Count the connected groups of land cells in a binary grid, using 4-directional "
            "adjacency."
        ),
        input_description=(
            "Line 1: rows and cols.\nThe next `rows` lines each hold `cols` characters of 0 or 1."
        ),
        output_description="The number of islands.",
        constraints=["1 <= rows, cols <= 300"],
        cases=[
            ("4 5\n11000\n11000\n00100\n00011\n", "3\n"),
            ("1 1\n0\n", "0\n"),
            ("1 1\n1\n", "1\n"),
            ("2 2\n11\n11\n", "1\n"),
        ],
        reference_solution="""import sys
lines = sys.stdin.read().split()
rows, cols = int(lines[0]), int(lines[1])
grid = [list(row) for row in lines[2:2 + rows]]
islands = 0
for r in range(rows):
    for c in range(cols):
        if grid[r][c] != "1":
            continue
        islands += 1
        stack = [(r, c)]
        grid[r][c] = "0"
        while stack:
            y, x = stack.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == "1":
                    grid[ny][nx] = "0"
                    stack.append((ny, nx))
print(islands)
""",
        editorial=(
            "Every unvisited land cell starts a flood fill that sinks its whole island, so the "
            "number of flood fills is the number of islands. O(rows * cols)."
        ),
    ),
    P(
        slug="course-schedule",
        title="Course Schedule",
        difficulty="medium",
        category="graphs",
        summary=(
            "Given prerequisite pairs `a b` meaning course b must precede course a, decide "
            "whether every course can be completed."
        ),
        input_description=(
            "Line 1: numCourses and m, the number of prerequisite pairs.\nThe next m lines each "
            "hold a pair `a b`."
        ),
        output_description="`true` if all courses can be finished, otherwise `false`.",
        constraints=["1 <= numCourses <= 100000", "0 <= m <= 100000"],
        cases=[
            ("2 1\n1 0\n", "true\n"),
            ("2 2\n1 0\n0 1\n", "false\n"),
            ("1 0\n", "true\n"),
            ("3 2\n1 0\n2 1\n", "true\n"),
        ],
        reference_solution="""import sys
from collections import deque
data = list(map(int, sys.stdin.read().split()))
courses, m = data[0], data[1]
adjacency = [[] for _ in range(courses)]
indegree = [0] * courses
for i in range(m):
    a, b = data[2 + 2 * i], data[3 + 2 * i]
    adjacency[b].append(a)
    indegree[a] += 1
queue = deque(node for node in range(courses) if indegree[node] == 0)
visited = 0
while queue:
    node = queue.popleft()
    visited += 1
    for neighbour in adjacency[node]:
        indegree[neighbour] -= 1
        if indegree[neighbour] == 0:
            queue.append(neighbour)
print("true" if visited == courses else "false")
""",
        editorial=(
            "Kahn's topological sort repeatedly removes a course with no outstanding "
            "prerequisites. If some courses never reach in-degree zero, the graph has a cycle."
        ),
    ),
    P(
        slug="graph-valid-tree",
        title="Graph Valid Tree",
        difficulty="medium",
        category="graphs",
        summary=(
            "Decide whether an undirected graph is a tree: fully connected and free of cycles."
        ),
        input_description=(
            "Line 1: n, the number of nodes labelled 0..n-1, and m, the number of edges.\n"
            "The next m lines each hold an edge `u v`."
        ),
        output_description="`true` if the graph is a valid tree, otherwise `false`.",
        constraints=["1 <= n <= 100000", "0 <= m <= 100000", "No self-loops."],
        cases=[
            ("5 4\n0 1\n0 2\n0 3\n1 4\n", "true\n"),
            ("5 5\n0 1\n1 2\n2 3\n1 3\n1 4\n", "false\n"),
            ("1 0\n", "true\n"),
            ("4 2\n0 1\n2 3\n", "false\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n, m = data[0], data[1]
if m != n - 1:
    print("false")
else:
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    ok = True
    for i in range(m):
        u, v = data[2 + 2 * i], data[3 + 2 * i]
        root_u, root_v = find(u), find(v)
        if root_u == root_v:
            ok = False
            break
        parent[root_u] = root_v
    print("true" if ok else "false")
""",
        editorial=(
            "A tree on n nodes has exactly n-1 edges and no cycle. Check the edge count first, "
            "then union-find every edge; a union of two already-connected nodes reveals a cycle."
        ),
    ),
    P(
        slug="dijkstra-shortest-path",
        title="Dijkstra Shortest Path",
        difficulty="hard",
        category="graphs",
        summary=(
            "Find the cost of the cheapest route between two nodes in a directed, "
            "non-negatively weighted graph."
        ),
        input_description=(
            "Line 1: n, m, source and target.\nThe next m lines each hold a directed edge "
            "`u v w`."
        ),
        output_description="The minimum total weight from source to target, or -1 if unreachable.",
        constraints=["1 <= n <= 100000", "0 <= m <= 200000", "0 <= w <= 10^9"],
        cases=[
            ("4 4 0 3\n0 1 1\n1 2 2\n2 3 3\n0 3 10\n", "6\n"),
            ("3 1 0 2\n0 1 5\n", "-1\n"),
            ("2 1 0 1\n0 1 7\n", "7\n"),
            ("5 6 0 4\n0 1 2\n0 2 4\n1 2 1\n1 3 7\n2 4 3\n3 4 1\n", "6\n"),
        ],
        reference_solution="""import sys
import heapq
data = list(map(int, sys.stdin.read().split()))
n, m, source, target = data[0], data[1], data[2], data[3]
adjacency = [[] for _ in range(n)]
for i in range(m):
    u, v, w = data[4 + 3 * i], data[5 + 3 * i], data[6 + 3 * i]
    adjacency[u].append((v, w))
distance = [None] * n
heap = [(0, source)]
while heap:
    cost, node = heapq.heappop(heap)
    if distance[node] is not None:
        continue
    distance[node] = cost
    for neighbour, weight in adjacency[node]:
        if distance[neighbour] is None:
            heapq.heappush(heap, (cost + weight, neighbour))
print(distance[target] if distance[target] is not None else -1)
""",
        editorial=(
            "Dijkstra with a binary heap settles nodes in increasing distance order. Because all "
            "weights are non-negative, the first time a node is popped its distance is final. "
            "O((n + m) log n)."
        ),
    ),
    # ---------------------------------------------------- dynamic programming
    P(
        slug="climbing-stairs",
        title="Climbing Stairs",
        difficulty="easy",
        category="dynamic programming",
        summary="Count the distinct ways to climb n stairs taking one or two steps at a time.",
        input_description="A single line containing n.",
        output_description="The number of distinct ways to reach the top.",
        constraints=["1 <= n <= 45"],
        cases=[("2\n", "2\n"), ("3\n", "3\n"), ("1\n", "1\n"), ("5\n", "8\n")],
        reference_solution="""import sys
n = int(sys.stdin.read().split()[0])
a, b = 1, 1
for _ in range(n - 1):
    a, b = b, a + b
print(b)
""",
        editorial=(
            "The count satisfies `f(n) = f(n-1) + f(n-2)` — the Fibonacci recurrence — so two "
            "rolling variables suffice."
        ),
    ),
    P(
        slug="house-robber",
        title="House Robber",
        difficulty="medium",
        category="dynamic programming",
        summary=("Maximise the loot from a row of houses without robbing two adjacent houses."),
        input_description="Line 1: n.\nLine 2: n space-separated non-negative values.",
        output_description="The maximum amount that can be robbed.",
        constraints=["1 <= n <= 100000", "0 <= value <= 10^4"],
        cases=[
            ("4\n1 2 3 1\n", "4\n"),
            ("5\n2 7 9 3 1\n", "12\n"),
            ("1\n5\n", "5\n"),
            ("4\n2 1 1 2\n", "4\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
skip = take = 0
for value in data[1:1 + n]:
    skip, take = max(skip, take), skip + value
print(max(skip, take))
""",
        editorial=(
            "Track two running totals: the best if the previous house was robbed and the best if "
            "it was not. O(n) time, O(1) space."
        ),
    ),
    P(
        slug="longest-increasing-subsequence",
        title="Longest Increasing Subsequence",
        difficulty="medium",
        category="dynamic programming",
        summary="Find the length of the longest strictly increasing subsequence.",
        input_description="Line 1: n.\nLine 2: n space-separated integers.",
        output_description="The length of the longest strictly increasing subsequence.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("8\n10 9 2 5 3 7 101 18\n", "4\n"),
            ("6\n0 1 0 3 2 3\n", "4\n"),
            ("7\n7 7 7 7 7 7 7\n", "1\n"),
            ("1\n4\n", "1\n"),
        ],
        reference_solution="""import sys
from bisect import bisect_left
data = list(map(int, sys.stdin.read().split()))
n = data[0]
tails = []
for value in data[1:1 + n]:
    position = bisect_left(tails, value)
    if position == len(tails):
        tails.append(value)
    else:
        tails[position] = value
print(len(tails))
""",
        editorial=(
            "Keep `tails[i]` as the smallest possible tail of an increasing subsequence of length "
            "i+1. Binary searching the insertion point gives O(n log n)."
        ),
    ),
    P(
        slug="coin-change",
        title="Coin Change",
        difficulty="medium",
        category="dynamic programming",
        summary="Find the fewest coins that add up to an amount, with unlimited coins of each type.",
        input_description="Line 1: n and amount.\nLine 2: n space-separated coin denominations.",
        output_description="The minimum number of coins, or -1 if the amount cannot be formed.",
        constraints=["1 <= n <= 100", "0 <= amount <= 10000"],
        cases=[
            ("3 11\n1 2 5\n", "3\n"),
            ("1 3\n2\n", "-1\n"),
            ("1 0\n1\n", "0\n"),
            ("2 6\n1 3\n", "2\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n, amount = data[0], data[1]
coins = data[2:2 + n]
INF = amount + 1
best = [0] + [INF] * amount
for value in range(1, amount + 1):
    for coin in coins:
        if coin <= value:
            best[value] = min(best[value], best[value - coin] + 1)
print(best[amount] if best[amount] < INF else -1)
""",
        editorial=(
            "Unbounded knapsack: `best[v]` is the fewest coins for value v, built up from smaller "
            "values. O(amount * n)."
        ),
    ),
    P(
        slug="jump-game",
        title="Jump Game",
        difficulty="medium",
        category="greedy",
        summary=(
            "Each value is the maximum jump length from that index. Decide whether the last "
            "index is reachable from the first."
        ),
        input_description="Line 1: n.\nLine 2: n space-separated non-negative jump lengths.",
        output_description="`true` if the last index is reachable, otherwise `false`.",
        constraints=["1 <= n <= 100000"],
        cases=[
            ("5\n2 3 1 1 4\n", "true\n"),
            ("5\n3 2 1 0 4\n", "false\n"),
            ("1\n0\n", "true\n"),
            ("4\n2 0 1 1\n", "true\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
nums = data[1:1 + n]
reach = 0
ok = True
for index, jump in enumerate(nums):
    if index > reach:
        ok = False
        break
    reach = max(reach, index + jump)
print("true" if ok else "false")
""",
        editorial=(
            "Sweep left to right tracking the furthest reachable index. Falling behind that "
            "frontier means the end is unreachable. O(n)."
        ),
    ),
    P(
        slug="min-meeting-rooms",
        title="Minimum Meeting Rooms",
        difficulty="medium",
        category="greedy",
        summary=(
            "Given meeting intervals `[start, end)`, find the fewest rooms needed to hold them "
            "all."
        ),
        input_description="Line 1: n.\nThe next n lines each hold `start end`.",
        output_description="The minimum number of rooms required.",
        constraints=["1 <= n <= 100000", "0 <= start < end <= 10^9"],
        cases=[
            ("3\n0 30\n5 10\n15 20\n", "2\n"),
            ("2\n7 10\n2 4\n", "1\n"),
            ("1\n1 5\n", "1\n"),
            ("4\n1 10\n2 7\n3 19\n8 12\n", "3\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
events = []
for i in range(n):
    start, end = data[1 + 2 * i], data[2 + 2 * i]
    events.append((start, 1))
    events.append((end, -1))
events.sort()
active = 0
rooms = 0
for _, delta in events:
    active += delta
    rooms = max(rooms, active)
print(rooms)
""",
        editorial=(
            "Turn each meeting into a +1 start event and a -1 end event, sort by time, and sweep. "
            "The peak concurrent count is the room requirement. Ends sort before starts at the "
            "same instant, so back-to-back meetings share a room."
        ),
    ),
    P(
        slug="merge-intervals",
        title="Merge Intervals",
        difficulty="medium",
        category="sorting",
        summary="Merge all overlapping closed intervals and report how many remain.",
        input_description="Line 1: n.\nThe next n lines each hold `start end`.",
        output_description="The number of intervals after merging.",
        constraints=["1 <= n <= 100000", "start <= end"],
        cases=[
            ("4\n1 3\n2 6\n8 10\n15 18\n", "3\n"),
            ("1\n1 4\n", "1\n"),
            ("2\n1 4\n4 5\n", "1\n"),
            ("2\n1 2\n3 4\n", "2\n"),
        ],
        reference_solution="""import sys
data = list(map(int, sys.stdin.read().split()))
n = data[0]
intervals = sorted(
    (data[1 + 2 * i], data[2 + 2 * i]) for i in range(n)
)
merged = 0
current_end = None
for start, end in intervals:
    if current_end is None or start > current_end:
        merged += 1
        current_end = end
    else:
        current_end = max(current_end, end)
print(merged)
""",
        editorial=(
            "Sort by start, then extend the current interval whenever the next one begins before "
            "it ends. O(n log n), dominated by the sort."
        ),
    ),
    # --------------------------------------------------------- backtracking
    P(
        slug="generate-parentheses",
        title="Generate Parentheses Count",
        difficulty="medium",
        category="backtracking",
        summary="Count the well-formed parenthesis strings that use exactly n pairs.",
        input_description="A single line containing n.",
        output_description="The number of valid parenthesis strings.",
        constraints=["0 <= n <= 15"],
        cases=[("1\n", "1\n"), ("3\n", "5\n"), ("0\n", "1\n"), ("4\n", "14\n")],
        reference_solution="""import sys
n = int(sys.stdin.read().split()[0])


def count(open_used: int, close_used: int) -> int:
    if open_used == n and close_used == n:
        return 1
    total = 0
    if open_used < n:
        total += count(open_used + 1, close_used)
    if close_used < open_used:
        total += count(open_used, close_used + 1)
    return total


print(count(0, 0))
""",
        editorial=(
            "Backtrack while keeping the number of closing brackets at or below the opening "
            "count. The total is the nth Catalan number."
        ),
    ),
    P(
        slug="permutations-count",
        title="Permutations Count",
        difficulty="medium",
        category="backtracking",
        summary="Count the distinct orderings of n distinct values.",
        input_description="A single line containing n.",
        output_description="The number of permutations, n!.",
        constraints=["0 <= n <= 20"],
        cases=[("3\n", "6\n"), ("1\n", "1\n"), ("0\n", "1\n"), ("4\n", "24\n")],
        reference_solution="""import sys
from math import factorial
print(factorial(int(sys.stdin.read().split()[0])))
""",
        editorial=(
            "Backtracking places each unused value in the next slot, producing n! leaves; the "
            "count itself is just the factorial."
        ),
    ),
]


CATALOG_BY_SLUG = {problem.slug: problem for problem in CATALOG}
