from __future__ import annotations

import re
from textwrap import dedent


def _text(value: str) -> str:
    return dedent(value).strip()


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "problem"


def _code(python: str, cpp: str, java: str) -> dict[str, str]:
    return {
        "Python": _text(python),
        "C++": _text(cpp),
        "Java": _text(java),
    }


def _mcq(question_id: str, prompt: str, options: list[str], answer_index: int, explanation: str) -> dict:
    return {
        "id": question_id,
        "prompt": _text(prompt),
        "options": options,
        "answer_index": answer_index,
        "explanation": _text(explanation),
    }


PATTERN_LIBRARY = {
    "hash_lookup": {
        "label": "Hash map lookup",
        "approach": "Store previously seen values in a hash map and use O(1) expected lookup to find the required complement or state.",
        "hints": [
            "Ask what fact from earlier elements would immediately solve the current step.",
            "A hash map lets you trade space for faster lookup.",
        ],
        "keywords": {
            "Python": ["dict", "for", "return", "lookup"],
            "C++": ["unordered_map", "for", "return", "count"],
            "Java": ["HashMap", "for", "return", "containsKey"],
        },
        "steps": [
            "Unpack the payload into the working inputs named in the prompt.",
            "Create the lookup structure that stores previously seen state.",
            "Scan once, solve the current position with the stored state, then update the map.",
            "Return the required answer as soon as the invariant is satisfied.",
        ],
    },
    "running_best": {
        "label": "Running best scan",
        "approach": "Maintain the best state seen so far while scanning left to right, updating the answer in O(n) time.",
        "hints": [
            "Write down what the best historical value means before coding.",
            "Each new element either improves the tracked state or uses it to improve the answer.",
        ],
        "keywords": {
            "Python": ["best", "for", "min", "max"],
            "C++": ["best", "for", "min", "max"],
            "Java": ["best", "for", "Math.min", "Math.max"],
        },
        "steps": [
            "Track the best historical candidate you need for future decisions.",
            "Update the answer using the current element and the historical state.",
            "Refresh the tracked state before moving to the next iteration.",
        ],
    },
    "prefix_suffix": {
        "label": "Prefix and suffix accumulation",
        "approach": "Precompute or stream prefix and suffix information so every position can answer its query without re-scanning the array.",
        "hints": [
            "Ask what information from the left and right is needed at each index.",
            "Streaming prefix and suffix passes often avoids division or nested loops.",
        ],
        "keywords": {
            "Python": ["prefix", "suffix", "range", "return"],
            "C++": ["prefix", "suffix", "vector", "return"],
            "Java": ["prefix", "suffix", "array", "return"],
        },
        "steps": [
            "Build the left-to-right contribution first.",
            "Combine it with the right-to-left contribution on a second pass.",
            "Return the final transformed array.",
        ],
    },
    "kadane": {
        "label": "Dynamic running subarray",
        "approach": "At each index choose between extending the previous contribution or starting a fresh segment, then keep the global best.",
        "hints": [
            "Write down what the best segment ending exactly here means.",
            "The local decision is usually max(start new, extend old).",
        ],
        "keywords": {
            "Python": ["current", "best", "max", "for"],
            "C++": ["current", "best", "max", "for"],
            "Java": ["current", "best", "Math.max", "for"],
        },
        "steps": [
            "Track the best value ending at the current position.",
            "Update the global answer after each step.",
            "Return the best global segment.",
        ],
    },
    "interval_merge": {
        "label": "Sort and merge intervals",
        "approach": "Sort intervals by starting point, then either extend the current merged interval or push a new one.",
        "hints": [
            "After sorting, overlap decisions become local.",
            "Keep one active interval and grow it while ranges intersect.",
        ],
        "keywords": {
            "Python": ["sort", "append", "max", "interval"],
            "C++": ["sort", "push_back", "max", "interval"],
            "Java": ["sort", "add", "Math.max", "interval"],
        },
        "steps": [
            "Sort the intervals by start time.",
            "Walk through the sorted list and merge overlaps into one active interval.",
            "Append completed intervals to the answer.",
        ],
    },
    "matrix_marking": {
        "label": "In-place matrix marking",
        "approach": "Use the first row and first column or a sentinel structure to mark which rows and columns need a bulk update.",
        "hints": [
            "Try to record future row/column work without scanning repeatedly.",
            "The first row and first column can act as compact storage if handled carefully.",
        ],
        "keywords": {
            "Python": ["row", "col", "matrix", "for"],
            "C++": ["row", "col", "matrix", "for"],
            "Java": ["row", "col", "matrix", "for"],
        },
        "steps": [
            "Record which rows and columns must change.",
            "Apply the bulk update after the discovery pass.",
            "Protect the marker row or column with separate booleans when needed.",
        ],
    },
    "two_pointer_scan": {
        "label": "Two-pointer scan",
        "approach": "Use two moving indices that shrink or expand the search space based on the current condition.",
        "hints": [
            "Decide what the left pointer guarantees and what the right pointer guarantees.",
            "Move the pointer whose change can improve the answer or restore validity.",
        ],
        "keywords": {
            "Python": ["left", "right", "while", "max"],
            "C++": ["left", "right", "while", "max"],
            "Java": ["left", "right", "while", "Math.max"],
        },
        "steps": [
            "Initialize left and right boundaries from the problem statement.",
            "Evaluate the current window or pair, then move the pointer that preserves the invariant.",
            "Stop when the search space is exhausted.",
        ],
    },
    "frequency_count": {
        "label": "Frequency counting",
        "approach": "Convert the input into counts or signatures, then answer the question using those aggregated counts.",
        "hints": [
            "Ask whether exact order matters or only multiplicity matters.",
            "A frequency map or fixed-size array often simplifies the logic.",
        ],
        "keywords": {
            "Python": ["counts", "get", "for", "return"],
            "C++": ["counts", "for", "return", "unordered_map"],
            "Java": ["counts", "getOrDefault", "for", "return"],
        },
        "steps": [
            "Build the frequency representation for the relevant input.",
            "Use the counts to verify the target condition.",
            "Return the boolean or grouped answer.",
        ],
    },
    "sliding_window": {
        "label": "Sliding window",
        "approach": "Expand a right pointer to gather enough information, then shrink the left pointer while preserving the window condition.",
        "hints": [
            "Define what makes a window valid before coding it.",
            "Count updates on both edges should be O(1).",
        ],
        "keywords": {
            "Python": ["left", "right", "window", "while"],
            "C++": ["left", "right", "window", "while"],
            "Java": ["left", "right", "window", "while"],
        },
        "steps": [
            "Expand the window with the right pointer.",
            "While the constraint breaks or a tighter answer is possible, move the left pointer.",
            "Update the best answer whenever the window satisfies the rule.",
        ],
    },
    "center_expand": {
        "label": "Expand around center",
        "approach": "Treat each index or gap as a potential center and expand outward while the structure remains valid.",
        "hints": [
            "Odd and even centers usually need separate consideration.",
            "Expansion stops at the first mismatch.",
        ],
        "keywords": {
            "Python": ["while", "left", "right", "slice"],
            "C++": ["while", "left", "right", "substr"],
            "Java": ["while", "left", "right", "substring"],
        },
        "steps": [
            "Generate every candidate center.",
            "Expand outward while the center remains valid.",
            "Keep the longest or best substring seen so far.",
        ],
    },
    "signature_grouping": {
        "label": "Canonical signature grouping",
        "approach": "Map each object to a canonical signature such as a sorted key or frequency tuple, then group identical signatures together.",
        "hints": [
            "Equivalent answers should share exactly the same key.",
            "Choose a signature that is easy to build and compare.",
        ],
        "keywords": {
            "Python": ["sorted", "setdefault", "dict", "append"],
            "C++": ["sort", "unordered_map", "push_back", "vector"],
            "Java": ["Arrays.sort", "HashMap", "computeIfAbsent", "add"],
        },
        "steps": [
            "Create a canonical signature for each item.",
            "Insert the item into the bucket for that signature.",
            "Return the grouped buckets.",
        ],
    },
    "reverse_list": {
        "label": "Iterative pointer reversal",
        "approach": "Walk through the linked list with previous, current, and next pointers to reverse links in place.",
        "hints": [
            "Save the next pointer before changing any links.",
            "Say out loud what each pointer owns after every assignment.",
        ],
        "keywords": {
            "Python": ["prev", "current", "next", "return"],
            "C++": ["prev", "current", "nextNode", "return"],
            "Java": ["prev", "current", "nextNode", "return"],
        },
        "steps": [
            "Initialize previous to null and current to the head.",
            "Save the next pointer, reverse the current link, then advance.",
            "Return the final previous pointer as the new head.",
        ],
    },
    "fast_slow": {
        "label": "Fast and slow pointers",
        "approach": "Use two pointers moving at different speeds to detect cycles, find middles, or split lists safely.",
        "hints": [
            "The fast pointer usually moves twice as quickly as the slow pointer.",
            "Check the null conditions before advancing the fast pointer.",
        ],
        "keywords": {
            "Python": ["slow", "fast", "while", "return"],
            "C++": ["slow", "fast", "while", "return"],
            "Java": ["slow", "fast", "while", "return"],
        },
        "steps": [
            "Initialize both pointers from the head.",
            "Advance the fast pointer twice and the slow pointer once while the structure allows it.",
            "Use the meeting or stopping condition to produce the answer.",
        ],
    },
    "list_merge": {
        "label": "Dummy-node merge",
        "approach": "Attach the next smallest or next required node to a dummy anchor so head-edge cases disappear.",
        "hints": [
            "A dummy node keeps the merge shape identical from start to finish.",
            "Advance only the pointer that provided the chosen node.",
        ],
        "keywords": {
            "Python": ["dummy", "tail", "while", "return"],
            "C++": ["dummy", "tail", "while", "return"],
            "Java": ["dummy", "tail", "while", "return"],
        },
        "steps": [
            "Create a dummy node and a tail pointer.",
            "Attach the next chosen node to tail, then advance the consumed list.",
            "Return dummy.next when the merge finishes.",
        ],
    },
    "reorder_weave": {
        "label": "Split, reverse, and weave",
        "approach": "Find the middle, reverse the second half, then stitch the two halves together in alternating order.",
        "hints": [
            "The middle split is usually done with fast and slow pointers.",
            "Reversal plus weaving turns a hard-looking list mutation into two standard phases.",
        ],
        "keywords": {
            "Python": ["slow", "fast", "prev", "while"],
            "C++": ["slow", "fast", "prev", "while"],
            "Java": ["slow", "fast", "prev", "while"],
        },
        "steps": [
            "Split the structure into two halves.",
            "Reverse the second half.",
            "Weave nodes from the first and second halves together.",
        ],
    },
    "monotonic_stack": {
        "label": "Monotonic stack",
        "approach": "Keep unresolved indices in sorted order so the next larger or smaller event can be answered when the order breaks.",
        "hints": [
            "Store indices when future distances or widths matter.",
            "Popping resolves work for the element at the top.",
        ],
        "keywords": {
            "Python": ["stack", "while", "append", "pop"],
            "C++": ["stack", "while", "push", "pop"],
            "Java": ["Deque", "while", "push", "pop"],
        },
        "steps": [
            "Push unresolved indices while the monotonic property holds.",
            "When the order breaks, pop and finalize answers for those positions.",
            "Continue until every element has been processed.",
        ],
    },
    "stack_parser": {
        "label": "Stack-based parsing",
        "approach": "Use a stack to represent unfinished nested work, then collapse it when a closing token or operator arrives.",
        "hints": [
            "The stack should store exactly the unresolved state you need later.",
            "Parse tokens in one pass whenever possible.",
        ],
        "keywords": {
            "Python": ["stack", "append", "pop", "return"],
            "C++": ["stack", "push", "pop", "return"],
            "Java": ["Deque", "push", "pop", "return"],
        },
        "steps": [
            "Push tokens or partial work when a nested structure opens.",
            "Collapse the stack when the matching close condition appears.",
            "Return the fully evaluated result.",
        ],
    },
    "queue_with_stacks": {
        "label": "Amortized queue with two stacks",
        "approach": "Push into one stack and move elements into the output stack only when needed so queue operations stay amortized O(1).",
        "hints": [
            "Delay the reversal until a pop or peek needs it.",
            "Each element crosses from input to output at most once.",
        ],
        "keywords": {
            "Python": ["in_stack", "out_stack", "append", "pop"],
            "C++": ["inStack", "outStack", "push", "pop"],
            "Java": ["inStack", "outStack", "push", "pop"],
        },
        "steps": [
            "Push new work into the input stack.",
            "If the output side is empty, pour elements across once.",
            "Pop or peek from the output stack.",
        ],
    },
    "bfs_grid": {
        "label": "Grid BFS",
        "approach": "Push one or many starting cells into a queue, then expand level by level through valid neighbors.",
        "hints": [
            "Use a queue for layered expansion.",
            "Mark a cell as visited the moment it enters the queue.",
        ],
        "keywords": {
            "Python": ["deque", "queue", "while", "append"],
            "C++": ["queue", "while", "push", "pop"],
            "Java": ["Queue", "while", "offer", "poll"],
        },
        "steps": [
            "Seed the queue with the starting positions.",
            "Pop from the queue, explore valid neighbors, and mark them immediately.",
            "Use BFS levels or timestamps when the problem asks for distance or time.",
        ],
    },
    "deque_window": {
        "label": "Monotonic deque window",
        "approach": "Use a deque to keep only candidates that can still become the best value for the current window.",
        "hints": [
            "Remove stale indices from the front and weaker candidates from the back.",
            "The front of the deque is always the answer for the active window.",
        ],
        "keywords": {
            "Python": ["deque", "window", "popleft", "append"],
            "C++": ["deque", "front", "back", "push_back"],
            "Java": ["Deque", "peekFirst", "peekLast", "offerLast"],
        },
        "steps": [
            "Discard indices that are outside the active window.",
            "Maintain the deque in answer-worthy order.",
            "Read the front when the window reaches full size.",
        ],
    },
    "backtracking_enumeration": {
        "label": "Backtracking enumeration",
        "approach": "Build the answer one choice at a time, recurse, then undo the choice before trying the next branch.",
        "hints": [
            "Write the recursive state in plain English first.",
            "Backtracking is choose, explore, un-choose.",
        ],
        "keywords": {
            "Python": ["path", "append", "pop", "dfs"],
            "C++": ["path", "push_back", "pop_back", "dfs"],
            "Java": ["path", "add", "remove", "dfs"],
        },
        "steps": [
            "Choose one valid option and add it to the current path.",
            "Recurse into the smaller remaining problem.",
            "Undo the choice so the next branch starts from a clean state.",
        ],
    },
    "backtracking_constraint": {
        "label": "Constraint backtracking",
        "approach": "Try a candidate only if it respects the partial constraints, then recurse deeper and roll back cleanly.",
        "hints": [
            "Pruning is the whole point. Reject invalid states early.",
            "Store fast lookup structures for used rows, columns, or characters when helpful.",
        ],
        "keywords": {
            "Python": ["path", "set", "remove", "dfs"],
            "C++": ["path", "set", "erase", "dfs"],
            "Java": ["path", "set", "remove", "dfs"],
        },
        "steps": [
            "Check whether the candidate keeps the partial solution valid.",
            "Record the candidate in the fast lookup structures.",
            "Recurse, then roll back every recorded choice.",
        ],
    },
    "binary_search": {
        "label": "Binary search",
        "approach": "Exploit sorted order by halving the search space after every comparison with the midpoint.",
        "hints": [
            "Decide whether the answer space is on the left or right of mid.",
            "Use left <= right or left < right consistently.",
        ],
        "keywords": {
            "Python": ["left", "right", "mid", "while"],
            "C++": ["left", "right", "mid", "while"],
            "Java": ["left", "right", "mid", "while"],
        },
        "steps": [
            "Initialize the searchable bounds.",
            "Compute the midpoint and decide which half can still contain the answer.",
            "Shrink the bounds until the answer is isolated.",
        ],
    },
    "divide_and_conquer": {
        "label": "Divide and conquer",
        "approach": "Split the problem into smaller independent pieces, solve them recursively, then combine the partial answers.",
        "hints": [
            "Define the base case before the split.",
            "The combine step is where the real invariant lives.",
        ],
        "keywords": {
            "Python": ["mid", "left", "right", "return"],
            "C++": ["mid", "left", "right", "return"],
            "Java": ["mid", "left", "right", "return"],
        },
        "steps": [
            "Split the input into smaller subproblems.",
            "Solve each piece recursively.",
            "Combine the solved pieces into the final answer.",
        ],
    },
    "prefix_hash": {
        "label": "Prefix sum with hashing",
        "approach": "Track prefix totals and use a hash map to ask whether a needed previous prefix has already appeared.",
        "hints": [
            "Translate the subarray condition into an equation on prefix sums.",
            "Store counts or earliest positions depending on the question.",
        ],
        "keywords": {
            "Python": ["prefix", "counts", "dict", "for"],
            "C++": ["prefix", "counts", "unordered_map", "for"],
            "Java": ["prefix", "counts", "HashMap", "for"],
        },
        "steps": [
            "Update the running prefix at each index.",
            "Use the hash map to detect whether the required historical prefix exists.",
            "Update the map after consuming the current element.",
        ],
    },
    "tree_traversal": {
        "label": "Tree traversal",
        "approach": "Express the answer in terms of the left subtree, the current node, and the right subtree, then choose DFS or BFS as needed.",
        "hints": [
            "Write what the recursive function returns before coding it.",
            "Traversal order determines what information is available at each step.",
        ],
        "keywords": {
            "Python": ["dfs", "node", "return", "queue"],
            "C++": ["dfs", "node", "return", "queue"],
            "Java": ["dfs", "node", "return", "queue"],
        },
        "steps": [
            "Choose the traversal order that exposes the needed information.",
            "Handle the null base case cleanly.",
            "Combine subtree results into the answer for the current node.",
        ],
    },
    "bst_property": {
        "label": "Binary-search-tree property",
        "approach": "Use the BST ordering invariant to prune the search space or validate bounds recursively.",
        "hints": [
            "Every node must respect all ancestral bounds, not only its parent.",
            "In-order traversal of a BST should be sorted.",
        ],
        "keywords": {
            "Python": ["left", "right", "lower", "upper"],
            "C++": ["left", "right", "lower", "upper"],
            "Java": ["left", "right", "lower", "upper"],
        },
        "steps": [
            "Carry the valid value range or in-order invariant through recursion.",
            "Reject any node that violates the BST rule.",
            "Return the final boolean or located node.",
        ],
    },
    "heap_selection": {
        "label": "Heap selection",
        "approach": "Maintain a heap containing only the candidates that can still matter to the answer.",
        "hints": [
            "Think in terms of keeping the best k elements instead of fully sorting everything.",
            "The heap top should represent the candidate you would discard next.",
        ],
        "keywords": {
            "Python": ["heapq", "heap", "heappush", "heappop"],
            "C++": ["priority_queue", "push", "pop", "top"],
            "Java": ["PriorityQueue", "offer", "poll", "peek"],
        },
        "steps": [
            "Choose whether the heap should be min-oriented or max-oriented.",
            "Push candidates into the heap and discard extras immediately.",
            "Return the heap-derived answer once all items are processed.",
        ],
    },
    "graph_traversal": {
        "label": "Graph traversal",
        "approach": "Model the structure as nodes and edges, then use DFS or BFS with visited tracking to explore it safely.",
        "hints": [
            "State clearly what a node and an edge mean in this problem.",
            "Visited tracking is mandatory when cycles are possible.",
        ],
        "keywords": {
            "Python": ["graph", "seen", "dfs", "queue"],
            "C++": ["graph", "seen", "dfs", "queue"],
            "Java": ["graph", "seen", "dfs", "queue"],
        },
        "steps": [
            "Build the adjacency representation.",
            "Traverse the graph while marking visited state.",
            "Use the traversal result to compute the final answer.",
        ],
    },
    "graph_bfs": {
        "label": "Breadth-first search",
        "approach": "Use a queue to expand the graph one layer at a time so the first visit to a state gives the minimum edge distance.",
        "hints": [
            "Push the starting state first and mark it visited immediately.",
            "BFS levels are especially useful when the question asks for the shortest number of moves.",
        ],
        "keywords": {
            "Python": ["deque", "queue", "popleft", "seen"],
            "C++": ["queue", "push", "pop", "seen"],
            "Java": ["Queue", "offer", "poll", "seen"],
        },
        "steps": [
            "Seed the queue with the starting state or all source states.",
            "Process the queue level by level while marking visited nodes.",
            "Return as soon as the target state is reached or the queue is exhausted.",
        ],
    },
    "dijkstra": {
        "label": "Dijkstra shortest path",
        "approach": "Use a min-heap of best-known distances and relax outgoing edges when a shorter path is found.",
        "hints": [
            "The first time you pop a node with its best distance, that distance is settled.",
            "Skip stale heap entries instead of trying to delete them early.",
        ],
        "keywords": {
            "Python": ["heapq", "dist", "graph", "while"],
            "C++": ["priority_queue", "dist", "graph", "while"],
            "Java": ["PriorityQueue", "dist", "graph", "while"],
        },
        "steps": [
            "Initialize all distances to infinity except the source.",
            "Pop the next closest node from the min-heap and relax its neighbors.",
            "Return the required shortest-path answer once the heap finishes or the target is settled.",
        ],
    },
    "topological_sort": {
        "label": "Topological ordering",
        "approach": "Track prerequisites with indegrees or DFS visitation states so you can detect cycles and produce a valid ordering.",
        "hints": [
            "Indegree zero means a task can be processed immediately.",
            "A directed cycle means no valid ordering exists.",
        ],
        "keywords": {
            "Python": ["indegree", "queue", "graph", "return"],
            "C++": ["indegree", "queue", "graph", "return"],
            "Java": ["indegree", "queue", "graph", "return"],
        },
        "steps": [
            "Build the directed graph and prerequisite counts.",
            "Process nodes whose prerequisites are already satisfied.",
            "Use the final processed count or order to decide whether the graph is valid.",
        ],
    },
    "dp_linear": {
        "label": "Linear dynamic programming",
        "approach": "Define the best answer ending at or up to each position, then update it from a small fixed set of previous states.",
        "hints": [
            "Say the state in plain English before writing the recurrence.",
            "Many linear DP problems can be compressed to O(1) extra space.",
        ],
        "keywords": {
            "Python": ["dp", "for", "max", "return"],
            "C++": ["dp", "for", "max", "return"],
            "Java": ["dp", "for", "Math.max", "return"],
        },
        "steps": [
            "Define the state and base case clearly.",
            "Compute each new state from a fixed number of earlier states.",
            "Return the final state or the best aggregate answer.",
        ],
    },
    "dp_sequence": {
        "label": "Sequence dynamic programming",
        "approach": "Use a table or optimized structure to compare prefixes or subsequences and carry the best relationship forward.",
        "hints": [
            "Think in terms of prefixes, not the full strings at once.",
            "Table dimensions often match the number of positions in the compared sequences.",
        ],
        "keywords": {
            "Python": ["dp", "range", "for", "return"],
            "C++": ["dp", "vector", "for", "return"],
            "Java": ["dp", "for", "return", "length"],
        },
        "steps": [
            "Let the state describe what the best answer means for shorter prefixes.",
            "Fill the table in an order that guarantees dependencies are ready.",
            "Read the final answer from the last cell or best tail structure.",
        ],
    },
    "dp_subset": {
        "label": "Subset-state dynamic programming",
        "approach": "Track which totals, counts, or subset states are achievable while processing items one by one.",
        "hints": [
            "Subset DP often updates the table backwards to avoid reusing an item twice.",
            "Booleans and counts are both useful depending on the question.",
        ],
        "keywords": {
            "Python": ["dp", "for", "range", "return"],
            "C++": ["dp", "for", "vector", "return"],
            "Java": ["dp", "for", "boolean", "return"],
        },
        "steps": [
            "Initialize the achievable base state.",
            "Update the table for each item without violating the reuse rule.",
            "Return whether or how well the target state can be formed.",
        ],
    },
    "greedy_reach": {
        "label": "Greedy reachability",
        "approach": "Track the best frontier reachable so far and decide locally whether the next move keeps the path alive or improves the answer.",
        "hints": [
            "A local choice is valid only if you can explain why it never hurts future decisions.",
            "The tracked frontier should summarize everything that matters.",
        ],
        "keywords": {
            "Python": ["reach", "for", "max", "return"],
            "C++": ["reach", "for", "max", "return"],
            "Java": ["reach", "for", "Math.max", "return"],
        },
        "steps": [
            "Track the farthest safe frontier after each position.",
            "Fail immediately if the current position is outside the frontier.",
            "Update the frontier or jump counter greedily.",
        ],
    },
    "greedy_interval": {
        "label": "Greedy interval scheduling",
        "approach": "Sort by the property that makes the local decision safe, then repeatedly choose the interval action that preserves future options.",
        "hints": [
            "Sorting by ending point is a common interval trick.",
            "Local choices are only valid when they maximize future flexibility.",
        ],
        "keywords": {
            "Python": ["sort", "for", "end", "count"],
            "C++": ["sort", "for", "end", "count"],
            "Java": ["sort", "for", "end", "count"],
        },
        "steps": [
            "Sort the intervals by the greedy key.",
            "Keep the locally best interval boundary.",
            "Count or build the answer while preserving as much future room as possible.",
        ],
    },
    "bit_xor": {
        "label": "Bitwise XOR",
        "approach": "Exploit the cancellation rule of XOR or direct bit comparisons to isolate the desired value.",
        "hints": [
            "x ^ x = 0 and x ^ 0 = x are the key identities.",
            "When pairs cancel, the leftover value is the answer.",
        ],
        "keywords": {
            "Python": ["xor", "^", "for", "return"],
            "C++": ["xor", "^", "for", "return"],
            "Java": ["xor", "^", "for", "return"],
        },
        "steps": [
            "Initialize the accumulator to zero.",
            "Combine each value with XOR.",
            "Return the leftover or bit-derived answer.",
        ],
    },
    "bit_count": {
        "label": "Bit counting",
        "approach": "Inspect or strip bits one by one, or reuse previous counts when the state transition is simple.",
        "hints": [
            "n & (n - 1) clears the lowest set bit.",
            "Binary patterns often let you build answers incrementally.",
        ],
        "keywords": {
            "Python": ["while", "&", "count", "return"],
            "C++": ["while", "&", "count", "return"],
            "Java": ["while", "&", "count", "return"],
        },
        "steps": [
            "Choose whether to count bits directly or build results from smaller numbers.",
            "Update the count or table using a constant-time bit trick.",
            "Return the final count or array.",
        ],
    },
    "bitmask_enumeration": {
        "label": "Bitmask enumeration",
        "approach": "Use the bits of an integer to represent choices, then iterate over masks to generate or test subsets.",
        "hints": [
            "Bit i answers whether item i is selected.",
            "The number of masks is usually 2^n, so this fits only for smaller n.",
        ],
        "keywords": {
            "Python": ["mask", "range", "&", "append"],
            "C++": ["mask", "for", "&", "push_back"],
            "Java": ["mask", "for", "&", "add"],
        },
        "steps": [
            "Loop over every mask from zero to the full subset count.",
            "Inspect each bit to decide which items are active.",
            "Build the subset or answer for that mask.",
        ],
    },
}


PATTERN_COMPLEXITIES = {
    "hash_lookup": ("O(n)", "O(n)"),
    "running_best": ("O(n)", "O(1)"),
    "prefix_suffix": ("O(n)", "O(n) including the output array"),
    "kadane": ("O(n)", "O(1)"),
    "interval_merge": ("O(n log n)", "O(n) for the merged output"),
    "matrix_marking": ("O(rows * cols)", "O(1) extra beyond the matrix or output"),
    "two_pointer_scan": ("O(n)", "O(1)"),
    "frequency_count": ("O(n)", "O(k) where k is the number of tracked symbols"),
    "sliding_window": ("O(n)", "O(k) where k is the tracked window state"),
    "center_expand": ("O(n^2)", "O(1)"),
    "signature_grouping": ("O(n * m log m)", "O(n * m)"),
    "reverse_list": ("O(n)", "O(1)"),
    "fast_slow": ("O(n)", "O(1)"),
    "list_merge": ("O(n + m)", "O(1) extra beyond the returned structure"),
    "reorder_weave": ("O(n)", "O(1)"),
    "monotonic_stack": ("O(n)", "O(n)"),
    "stack_parser": ("O(n)", "O(n)"),
    "queue_with_stacks": ("Amortized O(1) per operation", "O(n)"),
    "bfs_grid": ("O(rows * cols)", "O(rows * cols)"),
    "deque_window": ("O(n)", "O(k)"),
    "backtracking_enumeration": ("Exponential in the branching tree", "O(depth) plus the active path"),
    "backtracking_constraint": ("Exponential in the branching tree with pruning", "O(depth) plus constraint state"),
    "binary_search": ("O(log n)", "O(1)"),
    "divide_and_conquer": ("Usually O(n log n)", "O(log n) to O(n) depending on the combine step"),
    "prefix_hash": ("O(n)", "O(n)"),
    "tree_traversal": ("O(n)", "O(h) where h is the tree height"),
    "bst_property": ("O(n)", "O(h) where h is the tree height"),
    "heap_selection": ("O(n log k)", "O(k)"),
    "graph_traversal": ("O(V + E)", "O(V + E)"),
    "graph_bfs": ("O(V + E)", "O(V)"),
    "dijkstra": ("O((V + E) log V)", "O(V + E)"),
    "topological_sort": ("O(V + E)", "O(V)"),
    "dp_linear": ("O(n)", "O(n) or O(1) with compression"),
    "dp_sequence": ("O(n * m)", "O(n * m)"),
    "dp_subset": ("O(n * target)", "O(target) to O(n * target)"),
    "greedy_interval": ("O(n log n)", "O(1) to O(n)"),
    "greedy_reach": ("O(n)", "O(1)"),
    "bit_count": ("O(word_size) per value", "O(1)"),
    "bit_xor": ("O(n)", "O(1)"),
    "bitmask_enumeration": ("O(2^n * n)", "O(n) per constructed subset"),
}


def _difficulty_constraints(difficulty: str) -> list[str]:
    if difficulty == "Easy":
        return [
            "Prefer a clean linear or logarithmic solution over brute force.",
            "Handle empty or single-element edge cases explicitly.",
        ]
    if difficulty == "Medium":
        return [
            "The intended solution uses a named pattern or invariant.",
            "Be ready to explain why the state update stays O(1) or O(log n) per step.",
        ]
    return [
        "The optimized solution needs a stronger abstraction than the naive baseline.",
        "Your explanation should justify both the invariant and the complexity tradeoff.",
    ]


def _starter_code(function_name: str) -> dict[str, str]:
    return _code(
        f"""
        def {function_name}(payload):
            # payload contains the inputs exactly as described in the prompt.
            return None
        """,
        f"""
        auto {function_name}(auto payload) {{
            // payload contains the inputs exactly as described in the prompt.
            return 0;
        }}
        """,
        f"""
        Object {function_name}(Object payload) {{
            // payload contains the inputs exactly as described in the prompt.
            return null;
        }}
        """,
    )


def _solution_code(function_name: str, pattern_name: str) -> dict[str, str]:
    pattern = PATTERN_LIBRARY[pattern_name]
    steps = pattern["steps"]
    return _code(
        f"""
        def {function_name}(payload):
            # Optimized approach: {pattern["label"]}.
            # {steps[0]}
            # {steps[1]}
            # {steps[2]}
            # {steps[3] if len(steps) > 3 else "Return the final answer."}
            result = None
            return result
        """,
        f"""
        auto {function_name}(auto payload) {{
            // Optimized approach: {pattern["label"]}.
            // {steps[0]}
            // {steps[1]}
            // {steps[2]}
            // {steps[3] if len(steps) > 3 else "Return the final answer."}
            auto result = 0;
            return result;
        }}
        """,
        f"""
        Object {function_name}(Object payload) {{
            // Optimized approach: {pattern["label"]}.
            // {steps[0]}
            // {steps[1]}
            // {steps[2]}
            // {steps[3] if len(steps) > 3 else "Return the final answer."}
            Object result = null;
            return result;
        }}
        """,
    )


def _pseudo_code(function_name: str, pattern_name: str) -> str:
    steps = PATTERN_LIBRARY[pattern_name]["steps"]
    lines = [
        f"PROCEDURE {function_name}(payload)",
        "    1. Read and unpack the required inputs from payload.",
    ]
    for index, step in enumerate(steps, start=2):
        lines.append(f"    {index}. {step}")
    lines.append(f"    {len(steps) + 2}. Return the final answer.")
    return "\n".join(lines)


def _problem(
    topic_slug: str,
    title: str,
    difficulty: str,
    subtopic: str,
    pattern_name: str,
    statement: str,
    example_input: str,
    example_output: str,
    *,
    constraints: list[str] | None = None,
    hints: list[str] | None = None,
) -> dict:
    function_name = _slugify(title).replace("-", "_")
    pattern = PATTERN_LIBRARY[pattern_name]
    time_complexity, space_complexity = PATTERN_COMPLEXITIES[pattern_name]
    problem_id = f"{topic_slug}-{_slugify(title)}"
    merged_hints = list(pattern["hints"])
    if hints:
        merged_hints.extend(hints)
    return {
        "id": problem_id,
        "title": title,
        "difficulty": difficulty,
        "subtopic": subtopic,
        "statement": _text(statement),
        "constraints": constraints or _difficulty_constraints(difficulty),
        "hints": merged_hints,
        "examples": [
            {
                "input": example_input,
                "output": example_output,
                "explanation": f"Use the {pattern['label'].lower()} pattern to transform the example efficiently.",
            }
        ],
        "test_cases": [
            {"input": example_input, "output": example_output},
        ],
        "optimized_approach": _text(pattern["approach"]),
        "optimized_time_complexity": time_complexity,
        "optimized_space_complexity": space_complexity,
        "pseudo_code": _pseudo_code(function_name, pattern_name),
        "solution_summary": _text(
            f"""
            The intended strategy is {pattern["label"].lower()}. Start by writing the invariant,
            then apply these steps: {'; '.join(pattern["steps"])}.
            """
        ),
        "starter_code": _starter_code(function_name),
        "solution": _solution_code(function_name, pattern_name),
        "solution_keywords": pattern["keywords"],
        "pattern": pattern["label"],
    }


TOPIC_SPECS = [
    {
        "slug": "arrays",
        "title": "Arrays",
        "group": "Foundations",
        "subtopics": ["Prefix sums", "Intervals", "In-place transforms", "Greedy scans"],
        "concept": """
            Arrays reward clean indexing and invariant-driven thinking. They are where learners
            first see the tradeoff between brute force, prefix information, and state carried
            through a single pass.
        """,
        "time_complexity": [
            "Read by index: O(1)",
            "Linear scan: O(n)",
            "Middle insert/delete: O(n)",
        ],
        "space_complexity": "Usually O(n) for storage, with many optimized interview solutions targeting O(1) extra space.",
        "real_world_intuition": "Think of a spreadsheet row where position matters as much as value.",
        "alternative_approaches": [
            "Prefix/suffix accumulation for range-style questions",
            "Hashing when value lookup matters more than order",
            "Two pointers when the array is sorted or can be scanned from both ends",
        ],
        "interview_pitch": """
            Explain what each index or running value represents before you write the loop. If your
            invariant stays crisp, array problems become much easier to defend in an interview.
        """,
        "visual_intuition": """
            [4][1][7][9][2]
             ^      ^
           left   running best
        """,
        "implementations": _code(
            """
            def prefix_sums(nums):
                prefix = [0]
                for value in nums:
                    prefix.append(prefix[-1] + value)
                return prefix
            """,
            """
            vector<int> prefixSums(const vector<int>& nums) {
                vector<int> prefix = {0};
                for (int value : nums) prefix.push_back(prefix.back() + value);
                return prefix;
            }
            """,
            """
            List<Integer> prefixSums(int[] nums) {
                List<Integer> prefix = new ArrayList<>();
                prefix.add(0);
                for (int value : nums) prefix.add(prefix.get(prefix.size() - 1) + value);
                return prefix;
            }
            """,
        ),
        "practice_specs": [
            ("Two Sum", "Easy", "Hash lookup", "hash_lookup", "Return the indices of two elements whose sum equals the target.", "nums=[2,7,11,15], target=9", "[0, 1]"),
            ("Best Time to Buy and Sell Stock", "Easy", "Single scan", "running_best", "Return the maximum profit from one buy and one sell.", "prices=[7,1,5,3,6,4]", "5"),
            ("Product of Array Except Self", "Medium", "Prefix and suffix", "prefix_suffix", "Build the answer array without division.", "nums=[1,2,3,4]", "[24, 12, 8, 6]"),
            ("Maximum Subarray", "Medium", "Kadane", "kadane", "Return the maximum possible subarray sum.", "nums=[-2,1,-3,4,-1,2,1,-5,4]", "6"),
            ("Merge Intervals", "Medium", "Intervals", "interval_merge", "Merge all overlapping intervals and return the compact list.", "intervals=[[1,3],[2,6],[8,10],[15,18]]", "[[1, 6], [8, 10], [15, 18]]"),
            ("Set Matrix Zeroes", "Medium", "Matrix marking", "matrix_marking", "If any cell is zero, set its row and column to zero in place.", "matrix=[[1,1,1],[1,0,1],[1,1,1]]", "[[1,0,1],[0,0,0],[1,0,1]]"),
            ("Container With Most Water", "Medium", "Two pointers", "two_pointer_scan", "Choose two lines that form the maximum area container.", "height=[1,8,6,2,5,4,8,3,7]", "49"),
            ("Trapping Rain Water", "Hard", "Two pointers", "two_pointer_scan", "Return how much rain water can be trapped between bars.", "height=[0,1,0,2,1,0,1,3,2,1,2,1]", "6"),
            ("Rotate Array", "Easy", "In-place transform", "running_best", "Rotate the array to the right by k steps.", "nums=[1,2,3,4,5,6,7], k=3", "[5, 6, 7, 1, 2, 3, 4]"),
            ("Missing Number", "Easy", "Bit and math observation", "bit_xor", "Return the missing value from the range [0, n].", "nums=[3,0,1]", "2"),
        ],
        "mcqs": [
            _mcq("arrays-mcq-1", "Why is array index access O(1)?", ["Because arrays are always sorted.", "Because the address is computed directly from base plus offset.", "Because arrays never resize.", "Because arrays are trees."], 1, "Contiguous memory lets the runtime jump directly to the indexed cell."),
            _mcq("arrays-mcq-2", "Which technique is the first thing to try for range-sum style questions?", ["Backtracking", "Prefix sums", "Union find", "Greedy coloring"], 1, "Prefix information answers repeated range queries without re-scanning the array."),
        ],
    },
    {
        "slug": "strings",
        "title": "Strings",
        "group": "Foundations",
        "subtopics": ["Frequency maps", "Substrings", "Palindromes", "Pattern matching"],
        "concept": """
            String problems are really about representation. Once you decide whether order,
            multiplicity, or a sliding window matters most, the implementation usually follows.
        """,
        "time_complexity": [
            "Character access: O(1)",
            "Full scan: O(n)",
            "Common substring windows: O(n) to O(n log n)",
        ],
        "space_complexity": "Ranges from O(1) fixed alphabet counters to O(n) maps or buffers.",
        "real_world_intuition": "A string question is often a data-cleaning or streaming-validation problem in disguise.",
        "alternative_approaches": [
            "Frequency arrays for bounded alphabets",
            "Sliding windows for substring constraints",
            "Sorting or hashing for canonical comparison",
        ],
        "interview_pitch": """
            State what the window or frequency structure means before you move pointers. That keeps
            substring problems from turning into pointer spaghetti.
        """,
        "visual_intuition": """
            a b c a b c b b
            ^       ^
           left   right
        """,
        "implementations": _code(
            """
            def char_frequency(text):
                counts = {}
                for ch in text:
                    counts[ch] = counts.get(ch, 0) + 1
                return counts
            """,
            """
            unordered_map<char, int> charFrequency(const string& text) {
                unordered_map<char, int> counts;
                for (char ch : text) counts[ch]++;
                return counts;
            }
            """,
            """
            Map<Character, Integer> charFrequency(String text) {
                Map<Character, Integer> counts = new HashMap<>();
                for (char ch : text.toCharArray()) counts.put(ch, counts.getOrDefault(ch, 0) + 1);
                return counts;
            }
            """,
        ),
        "practice_specs": [
            ("Valid Anagram", "Easy", "Frequency maps", "frequency_count", "Return true if two strings are anagrams of each other.", "s='anagram', t='nagaram'", "True"),
            ("Valid Palindrome", "Easy", "Filtered scan", "two_pointer_scan", "Ignore non-alphanumeric characters and check whether the string reads the same both ways.", "s='A man, a plan, a canal: Panama'", "True"),
            ("Longest Substring Without Repeating Characters", "Medium", "Sliding window", "sliding_window", "Return the length of the longest substring with all distinct characters.", "s='abcabcbb'", "3"),
            ("Longest Palindromic Substring", "Medium", "Center expansion", "center_expand", "Return the longest palindromic substring.", "s='babad'", "'bab'"),
            ("Group Anagrams", "Medium", "Canonical signatures", "signature_grouping", "Group words that are anagrams of each other.", "strs=['eat','tea','tan','ate','nat','bat']", "[['eat','tea','ate'], ['tan','nat'], ['bat']]"),
            ("Find All Anagrams in a String", "Medium", "Sliding window", "sliding_window", "Return every starting index of an anagram of p inside s.", "s='cbaebabacd', p='abc'", "[0, 6]"),
            ("Minimum Window Substring", "Hard", "Sliding window", "sliding_window", "Return the smallest substring of s that covers every character of t.", "s='ADOBECODEBANC', t='ABC'", "'BANC'"),
            ("String to Integer (atoi)", "Medium", "Parsing", "stack_parser", "Implement the classic atoi conversion with overflow handling.", "s='   -42'", "-42"),
            ("Implement strStr", "Easy", "Pattern matching", "sliding_window", "Return the first index where needle appears in haystack.", "haystack='sadbutsad', needle='sad'", "0"),
            ("Encode and Decode Strings", "Medium", "Framing", "stack_parser", "Encode a list of strings into one string and decode it back safely.", "strs=['lint','code','love','you']", "['lint','code','love','you']"),
        ],
        "mcqs": [
            _mcq("strings-mcq-1", "What is the most natural tool for longest-valid-substring problems?", ["Sliding window", "Union find", "Floyd-Warshall", "Heap"], 0, "Sliding windows track a moving valid range in one pass."),
            _mcq("strings-mcq-2", "Why do anagram grouping problems often sort each word first?", ["To make every word shorter.", "To produce a canonical signature for equivalent words.", "To reduce the alphabet size.", "To avoid extra memory completely."], 1, "A canonical representation ensures all anagrams land in the same bucket."),
        ],
    },
    {
        "slug": "linked_list",
        "title": "Linked List",
        "group": "Foundations",
        "subtopics": ["Pointer reversal", "Fast/slow runners", "Dummy nodes", "List weaving"],
        "concept": """
            Linked lists are less about storage and more about safe pointer choreography. They are
            perfect training for mutating structure without losing track of ownership.
        """,
        "time_complexity": [
            "Traversal: O(n)",
            "Known-node insert/delete: O(1)",
            "Index access: O(n)",
        ],
        "space_complexity": "Usually O(1) extra for in-place pointer rewiring.",
        "real_world_intuition": "Imagine train cars where you can only follow the coupler to the next car.",
        "alternative_approaches": [
            "Dummy nodes to erase head-edge cases",
            "Fast/slow pointers for middle and cycle tasks",
            "Stacks when reverse access is conceptually simpler",
        ],
        "interview_pitch": """
            Narrate the pointers. If you can say where prev, current, and next point before and
            after a line, the solution stops feeling risky.
        """,
        "visual_intuition": """
            prev <- current -> next
        """,
        "implementations": _code(
            """
            def reverse_list(head):
                prev = None
                current = head
                while current:
                    nxt = current.next
                    current.next = prev
                    prev = current
                    current = nxt
                return prev
            """,
            """
            ListNode* reverseList(ListNode* head) {
                ListNode* prev = nullptr;
                ListNode* current = head;
                while (current) {
                    ListNode* nextNode = current->next;
                    current->next = prev;
                    prev = current;
                    current = nextNode;
                }
                return prev;
            }
            """,
            """
            ListNode reverseList(ListNode head) {
                ListNode prev = null;
                ListNode current = head;
                while (current != null) {
                    ListNode nextNode = current.next;
                    current.next = prev;
                    prev = current;
                    current = nextNode;
                }
                return prev;
            }
            """,
        ),
        "practice_specs": [
            ("Reverse Linked List", "Easy", "Pointer reversal", "reverse_list", "Reverse a singly linked list and return the new head.", "head=[1,2,3,4,5]", "[5,4,3,2,1]"),
            ("Linked List Cycle", "Easy", "Fast and slow", "fast_slow", "Return true if the linked list contains a cycle.", "head=[3,2,0,-4], pos=1", "True"),
            ("Merge Two Sorted Lists", "Easy", "Dummy node", "list_merge", "Merge two sorted linked lists and return the sorted merged list.", "list1=[1,2,4], list2=[1,3,4]", "[1,1,2,3,4,4]"),
            ("Remove Nth Node From End of List", "Medium", "Fast and slow", "fast_slow", "Delete the nth node from the end in one pass.", "head=[1,2,3,4,5], n=2", "[1,2,3,5]"),
            ("Reorder List", "Medium", "Weaving", "reorder_weave", "Reorder L0->L1->...->Ln into L0->Ln->L1->Ln-1...", "head=[1,2,3,4]", "[1,4,2,3]"),
            ("Palindrome Linked List", "Easy", "Half reverse", "reorder_weave", "Return true if the linked list reads the same forward and backward.", "head=[1,2,2,1]", "True"),
            ("Copy List With Random Pointer", "Hard", "Hash lookup", "hash_lookup", "Create a deep copy of a linked list where each node also stores a random pointer.", "head=[[7,null],[13,0],[11,4],[10,2],[1,0]]", "deep copy"),
            ("Add Two Numbers", "Medium", "Digit simulation", "list_merge", "Add two numbers stored in reverse-order linked lists.", "l1=[2,4,3], l2=[5,6,4]", "[7,0,8]"),
            ("Reverse Nodes in k-Group", "Hard", "Segment reversal", "reverse_list", "Reverse every group of k nodes and leave the last short group as-is.", "head=[1,2,3,4,5], k=2", "[2,1,4,3,5]"),
            ("Sort List", "Medium", "Merge sort", "divide_and_conquer", "Sort the linked list in O(n log n) time.", "head=[4,2,1,3]", "[1,2,3,4]"),
        ],
        "mcqs": [
            _mcq("linked-list-mcq-1", "Why do dummy nodes simplify many list problems?", ["They make every operation O(1).", "They remove special head-update cases.", "They avoid null checks completely.", "They sort the list."], 1, "A dummy anchor gives all splices the same shape, including the head."),
            _mcq("linked-list-mcq-2", "What is Floyd's cycle-detection idea?", ["Use recursion depth.", "Move two pointers at different speeds.", "Sort nodes by value.", "Reverse the list first."], 1, "A fast runner eventually laps a slow runner if a cycle exists."),
        ],
    },
    {
        "slug": "stack",
        "title": "Stack",
        "group": "Foundations",
        "subtopics": ["Parenthesis matching", "Monotonic stacks", "Expression parsing", "Undo state"],
        "concept": """
            Stacks model last-in-first-out work. They appear whenever the most recent unresolved
            item must be handled next.
        """,
        "time_complexity": [
            "Push: O(1)",
            "Pop: O(1)",
            "Peek: O(1)",
        ],
        "space_complexity": "Up to O(n) for stored unresolved work.",
        "real_world_intuition": "Think of browser history or nested folders waiting to be closed.",
        "alternative_approaches": [
            "Recursion when the call stack is acceptable",
            "Monotonic stacks for nearest-greater / nearest-smaller patterns",
            "Parsing stacks for nested expressions",
        ],
        "interview_pitch": """
            Say what the stack stores: raw values, indices, or unfinished work. Once that is clear,
            the push and pop rules become much easier to justify.
        """,
        "visual_intuition": """
            top -> [7]
                   [5]
                   [2]
        """,
        "implementations": _code(
            """
            def is_balanced(text):
                stack = []
                pairs = {')': '(', ']': '[', '}': '{'}
                for ch in text:
                    if ch in pairs.values():
                        stack.append(ch)
                    elif ch in pairs:
                        if not stack or stack.pop() != pairs[ch]:
                            return False
                return not stack
            """,
            """
            bool isBalanced(const string& text) {
                stack<char> st;
                unordered_map<char, char> pairs = {{')', '('}, {']', '['}, {'}', '{'}};
                for (char ch : text) {
                    if (ch == '(' || ch == '[' || ch == '{') st.push(ch);
                    else if (pairs.count(ch)) {
                        if (st.empty() || st.top() != pairs[ch]) return false;
                        st.pop();
                    }
                }
                return st.empty();
            }
            """,
            """
            boolean isBalanced(String text) {
                Deque<Character> stack = new ArrayDeque<>();
                Map<Character, Character> pairs = Map.of(')', '(', ']', '[', '}', '{');
                for (char ch : text.toCharArray()) {
                    if (ch == '(' || ch == '[' || ch == '{') stack.push(ch);
                    else if (pairs.containsKey(ch)) {
                        if (stack.isEmpty() || stack.pop() != pairs.get(ch)) return false;
                    }
                }
                return stack.isEmpty();
            }
            """,
        ),
        "practice_specs": [
            ("Valid Parentheses", "Easy", "Bracket matching", "stack_parser", "Return true if every opening bracket is closed correctly.", "s='({[]})'", "True"),
            ("Min Stack", "Medium", "Design stack", "monotonic_stack", "Design a stack that returns the minimum element in O(1).", "ops=['MinStack','push','push','push','getMin'], values=[[],[-2],[0],[-3],[]]", "-3"),
            ("Daily Temperatures", "Medium", "Monotonic stack", "monotonic_stack", "Return how many days you have to wait for a warmer temperature.", "temperatures=[73,74,75,71,69,72,76,73]", "[1,1,4,2,1,1,0,0]"),
            ("Evaluate Reverse Polish Notation", "Medium", "Expression evaluation", "stack_parser", "Evaluate the arithmetic value of a reverse-Polish expression.", "tokens=['2','1','+','3','*']", "9"),
            ("Largest Rectangle in Histogram", "Hard", "Monotonic stack", "monotonic_stack", "Return the area of the largest rectangle in a histogram.", "heights=[2,1,5,6,2,3]", "10"),
            ("Decode String", "Medium", "Nested parsing", "stack_parser", "Decode strings such as 3[a2[c]].", "s='3[a2[c]]'", "'accaccacc'"),
            ("Asteroid Collision", "Medium", "State resolution", "stack_parser", "Simulate collisions between moving asteroids.", "asteroids=[5,10,-5]", "[5,10]"),
            ("Simplify Path", "Medium", "Path parsing", "stack_parser", "Simplify a Unix-style file path.", "path='/home//foo/'", "'/home/foo'"),
            ("Remove K Digits", "Medium", "Greedy stack", "monotonic_stack", "Remove k digits to make the smallest possible number.", "num='1432219', k=3", "'1219'"),
            ("Basic Calculator", "Hard", "Expression parsing", "stack_parser", "Evaluate a string expression containing parentheses and signs.", "s='1 + (2 - (3 + 4))'", "-4"),
        ],
        "mcqs": [
            _mcq("stack-mcq-1", "What does a monotonic stack store?", ["Only sorted arrays.", "Unresolved candidates in a chosen sorted order.", "Only negative values.", "Visited nodes of a graph."], 1, "The stack preserves the order needed to answer the next-greater or next-smaller event."),
            _mcq("stack-mcq-2", "Which pattern naturally suggests a stack?", ["Most recent unmatched token matters.", "You need a shortest path in weighted edges.", "You need all-pairs distance.", "You are sorting with merge sort."], 0, "Stacks are for newest-unresolved-first problems."),
        ],
    },
    {
        "slug": "queue",
        "title": "Queue",
        "group": "Foundations",
        "subtopics": ["FIFO processing", "BFS layers", "Deque windows", "Scheduling"],
        "concept": """
            Queues model first-in-first-out work. Whenever processing order follows discovery order,
            a queue or deque is usually the right mental model.
        """,
        "time_complexity": [
            "Enqueue: O(1)",
            "Dequeue: O(1)",
            "Front read: O(1)",
        ],
        "space_complexity": "Up to O(n) for queued work.",
        "real_world_intuition": "Think of customer service tickets processed in the order they arrive.",
        "alternative_approaches": [
            "Deque when you need both-end updates",
            "Two stacks to emulate a queue",
            "Priority queue when priority matters more than arrival order",
        ],
        "interview_pitch": """
            Distinguish arrival order from priority order. That one choice usually separates queue
            problems from heap problems instantly.
        """,
        "visual_intuition": """
            front -> [job1][job2][job3] <- back
        """,
        "implementations": _code(
            """
            from collections import deque


            def bfs_levels(graph, start):
                queue = deque([start])
                seen = {start}
                order = []
                while queue:
                    node = queue.popleft()
                    order.append(node)
                    for neighbor in graph[node]:
                        if neighbor not in seen:
                            seen.add(neighbor)
                            queue.append(neighbor)
                return order
            """,
            """
            vector<int> bfsLevels(unordered_map<int, vector<int>>& graph, int start) {
                queue<int> q;
                unordered_set<int> seen = {start};
                vector<int> order;
                q.push(start);
                while (!q.empty()) {
                    int node = q.front();
                    q.pop();
                    order.push_back(node);
                    for (int neighbor : graph[node]) {
                        if (!seen.count(neighbor)) {
                            seen.insert(neighbor);
                            q.push(neighbor);
                        }
                    }
                }
                return order;
            }
            """,
            """
            List<Integer> bfsLevels(Map<Integer, List<Integer>> graph, int start) {
                Queue<Integer> queue = new ArrayDeque<>();
                Set<Integer> seen = new HashSet<>();
                List<Integer> order = new ArrayList<>();
                queue.offer(start);
                seen.add(start);
                while (!queue.isEmpty()) {
                    int node = queue.poll();
                    order.add(node);
                    for (int neighbor : graph.get(node)) {
                        if (!seen.contains(neighbor)) {
                            seen.add(neighbor);
                            queue.offer(neighbor);
                        }
                    }
                }
                return order;
            }
            """,
        ),
        "practice_specs": [
            ("Implement Queue Using Stacks", "Easy", "Design queue", "queue_with_stacks", "Design a queue using stack operations only.", "ops=['MyQueue','push','push','peek','pop'], values=[[],[1],[2],[],[]]", "1 then 1"),
            ("Rotting Oranges", "Medium", "Multi-source BFS", "bfs_grid", "Return the minutes needed to rot every orange, or -1 if impossible.", "grid=[[2,1,1],[1,1,0],[0,1,1]]", "4"),
            ("Sliding Window Maximum", "Hard", "Monotonic deque", "deque_window", "Return the maximum value in every window of size k.", "nums=[1,3,-1,-3,5,3,6,7], k=3", "[3,3,5,5,6,7]"),
            ("Design Circular Queue", "Medium", "Queue design", "queue_with_stacks", "Implement a fixed-size circular queue with O(1) operations.", "k=3, ops=['enQueue','enQueue','deQueue']", "True, True, True"),
            ("Number of Recent Calls", "Easy", "Window queue", "queue_with_stacks", "Count recent ping requests within the last 3000 milliseconds.", "calls=[1,100,3001,3002]", "[1,2,3,3]"),
            ("01 Matrix", "Medium", "Grid BFS", "bfs_grid", "Return the distance from every cell to the nearest zero.", "mat=[[0,0,0],[0,1,0],[1,1,1]]", "[[0,0,0],[0,1,0],[1,2,1]]"),
            ("Walls and Gates", "Medium", "Grid BFS", "bfs_grid", "Fill every empty room with the distance to its nearest gate.", "rooms=[[INF,-1,0,INF],[INF,INF,INF,-1],[INF,-1,INF,-1],[0,-1,INF,INF]]", "distances filled"),
            ("Open the Lock", "Medium", "State BFS", "graph_bfs", "Return the minimum number of moves needed to reach the target lock combination.", "deadends=['0201','0101','0102','1212','2002'], target='0202'", "6"),
            ("Perfect Squares", "Medium", "Level BFS", "graph_bfs", "Return the least number of perfect-square numbers that sum to n.", "n=12", "3"),
            ("Task Scheduler", "Medium", "Queue scheduling", "heap_selection", "Return the least intervals needed to schedule tasks with a cooldown.", "tasks=['A','A','A','B','B','B'], n=2", "8"),
        ],
        "mcqs": [
            _mcq("queue-mcq-1", "Why does BFS use a queue?", ["It prefers the deepest node first.", "It processes nodes in discovery order.", "It sorts neighbors automatically.", "It avoids visited state."], 1, "Breadth-first search expands the oldest frontier node first."),
            _mcq("queue-mcq-2", "What makes a deque different from a plain queue?", ["It stores only integers.", "It supports O(1) operations at both ends.", "It automatically stays sorted.", "It cannot be used for sliding windows."], 1, "A deque is a double-ended queue."),
        ],
    },
    {
        "slug": "recursion_backtracking",
        "title": "Recursion & Backtracking",
        "group": "Pattern Building",
        "subtopics": ["Decision trees", "Permutation search", "Constraint pruning", "Combinatorics"],
        "concept": """
            Backtracking is disciplined trial-and-error. You choose a branch, explore it fully,
            then rewind cleanly before trying the next branch.
        """,
        "time_complexity": [
            "Depends on branching factor and depth",
            "Pruning can collapse the practical search space dramatically",
        ],
        "space_complexity": "Usually O(depth) recursion stack plus the current path or board state.",
        "real_world_intuition": "Think of filling a puzzle where every wrong guess must be undone cleanly.",
        "alternative_approaches": [
            "Iterative DFS when recursion depth is risky",
            "Bitmasks for compact used-state tracking",
            "Dynamic programming when overlapping subproblems appear",
        ],
        "interview_pitch": """
            Say what one recursion level means. If one call represents "all completions from this
            partial path," the code becomes much easier to trust.
        """,
        "visual_intuition": """
            choose -> recurse -> un-choose
        """,
        "implementations": _code(
            """
            def subsets(nums):
                answer = []
                path = []

                def dfs(index):
                    if index == len(nums):
                        answer.append(path[:])
                        return
                    path.append(nums[index])
                    dfs(index + 1)
                    path.pop()
                    dfs(index + 1)

                dfs(0)
                return answer
            """,
            """
            void dfs(int index, vector<int>& nums, vector<int>& path, vector<vector<int>>& answer) {
                if (index == nums.size()) {
                    answer.push_back(path);
                    return;
                }
                path.push_back(nums[index]);
                dfs(index + 1, nums, path, answer);
                path.pop_back();
                dfs(index + 1, nums, path, answer);
            }
            """,
            """
            void dfs(int index, int[] nums, List<Integer> path, List<List<Integer>> answer) {
                if (index == nums.length) {
                    answer.add(new ArrayList<>(path));
                    return;
                }
                path.add(nums[index]);
                dfs(index + 1, nums, path, answer);
                path.remove(path.size() - 1);
                dfs(index + 1, nums, path, answer);
            }
            """,
        ),
        "practice_specs": [
            ("Subsets", "Easy", "Decision tree", "backtracking_enumeration", "Return every subset of the input array.", "nums=[1,2,3]", "[[],[1],[2],[3],[1,2],[1,3],[2,3],[1,2,3]]"),
            ("Permutations", "Medium", "Decision tree", "backtracking_enumeration", "Return every permutation of distinct numbers.", "nums=[1,2,3]", "all 6 permutations"),
            ("Combination Sum", "Medium", "Repeat choices", "backtracking_enumeration", "Return all combinations that sum to the target when numbers may be reused.", "candidates=[2,3,6,7], target=7", "[[2,2,3],[7]]"),
            ("Generate Parentheses", "Medium", "Constraint generation", "backtracking_constraint", "Generate every valid parenthesis string with n pairs.", "n=3", "['((()))','(()())','(())()','()(())','()()()']"),
            ("Word Search", "Medium", "Grid backtracking", "backtracking_constraint", "Return true if the word can be formed from adjacent board cells.", "board=[['A','B','C','E'],['S','F','C','S'],['A','D','E','E']], word='ABCCED'", "True"),
            ("Palindrome Partitioning", "Medium", "Partition search", "backtracking_constraint", "Partition the string so every piece is a palindrome.", "s='aab'", "[['a','a','b'], ['aa','b']]"),
            ("Letter Combinations of a Phone Number", "Medium", "Cartesian product", "backtracking_enumeration", "Return every possible letter combination for the input digits.", "digits='23'", "['ad','ae','af','bd','be','bf','cd','ce','cf']"),
            ("Restore IP Addresses", "Medium", "Bounded branching", "backtracking_constraint", "Return every valid IP address that can be built from the digits.", "s='25525511135'", "['255.255.11.135','255.255.111.35']"),
            ("N-Queens", "Hard", "Constraint board search", "backtracking_constraint", "Return all valid placements of n queens on an n x n board.", "n=4", "2 valid boards"),
            ("Sudoku Solver", "Hard", "Constraint board search", "backtracking_constraint", "Fill the Sudoku board in place.", "board=9x9 puzzle", "solved board"),
        ],
        "mcqs": [
            _mcq("backtracking-mcq-1", "What are the three verbs of classic backtracking?", ["Sort, merge, return", "Choose, explore, un-choose", "Push, pop, peek", "Hash, count, compare"], 1, "Backtracking is choose, recurse, and roll back."),
            _mcq("backtracking-mcq-2", "Why does pruning matter so much in backtracking?", ["It makes recursion iterative.", "It cuts away branches that can never lead to a valid answer.", "It sorts the answers automatically.", "It avoids copying lists."], 1, "The search tree is only feasible because invalid branches are cut early."),
        ],
    },
    {
        "slug": "searching_sorting",
        "title": "Searching & Sorting",
        "group": "Pattern Building",
        "subtopics": ["Binary search", "Partition logic", "Merge sort", "Ordering invariants"],
        "concept": """
            Searching and sorting problems are mostly about exploiting order. Once order exists,
            whole regions of the answer space become impossible and can be skipped.
        """,
        "time_complexity": [
            "Binary search: O(log n)",
            "Merge sort: O(n log n)",
            "Selection via partition: expected O(n)",
        ],
        "space_complexity": "Ranges from O(1) extra for in-place partition ideas to O(n) for merge-based solutions.",
        "real_world_intuition": "This is the difference between flipping through a sorted index and scanning every page.",
        "alternative_approaches": [
            "Binary search on answers, not only on arrays",
            "Divide and conquer when order can be created or preserved recursively",
            "Two-pointer post-processing on sorted data",
        ],
        "interview_pitch": """
            Say what order buys you. If you can explain which half becomes impossible after each
            comparison, binary-search style reasoning feels much more grounded.
        """,
        "visual_intuition": """
            left ... mid ... right
        """,
        "implementations": _code(
            """
            def binary_search(nums, target):
                left, right = 0, len(nums) - 1
                while left <= right:
                    mid = (left + right) // 2
                    if nums[mid] == target:
                        return mid
                    if nums[mid] < target:
                        left = mid + 1
                    else:
                        right = mid - 1
                return -1
            """,
            """
            int binarySearch(const vector<int>& nums, int target) {
                int left = 0;
                int right = static_cast<int>(nums.size()) - 1;
                while (left <= right) {
                    int mid = left + (right - left) / 2;
                    if (nums[mid] == target) return mid;
                    if (nums[mid] < target) left = mid + 1;
                    else right = mid - 1;
                }
                return -1;
            }
            """,
            """
            int binarySearch(int[] nums, int target) {
                int left = 0;
                int right = nums.length - 1;
                while (left <= right) {
                    int mid = left + (right - left) / 2;
                    if (nums[mid] == target) return mid;
                    if (nums[mid] < target) left = mid + 1;
                    else right = mid - 1;
                }
                return -1;
            }
            """,
        ),
        "practice_specs": [
            ("Binary Search", "Easy", "Sorted lookup", "binary_search", "Return the index of target in a sorted array, or -1 if absent.", "nums=[-1,0,3,5,9,12], target=9", "4"),
            ("Search in Rotated Sorted Array", "Medium", "Partition reasoning", "binary_search", "Search a rotated sorted array in O(log n).", "nums=[4,5,6,7,0,1,2], target=0", "4"),
            ("Find First and Last Position of Element in Sorted Array", "Medium", "Boundary binary search", "binary_search", "Return the first and last index of the target value.", "nums=[5,7,7,8,8,10], target=8", "[3, 4]"),
            ("Find Peak Element", "Medium", "Binary search on answer shape", "binary_search", "Return any index containing a peak element.", "nums=[1,2,1,3,5,6,4]", "1 or 5"),
            ("Sort Colors", "Medium", "Partitioning", "two_pointer_scan", "Sort an array containing 0, 1, and 2 in one pass.", "nums=[2,0,2,1,1,0]", "[0,0,1,1,2,2]"),
            ("Merge Sort", "Medium", "Divide and conquer", "divide_and_conquer", "Sort the array using merge sort.", "nums=[5,2,3,1]", "[1,2,3,5]"),
            ("Quick Select", "Medium", "Partitioning", "divide_and_conquer", "Return the kth smallest or kth largest element without fully sorting.", "nums=[3,2,1,5,6,4], k=2", "5"),
            ("Median of Two Sorted Arrays", "Hard", "Binary partition", "binary_search", "Return the median of two sorted arrays in logarithmic time.", "nums1=[1,3], nums2=[2]", "2.0"),
            ("Kth Smallest Element in a Sorted Matrix", "Medium", "Answer-space search", "binary_search", "Return the kth smallest element in a row-wise and column-wise sorted matrix.", "matrix=[[1,5,9],[10,11,13],[12,13,15]], k=8", "13"),
            ("Count Inversions", "Hard", "Merge counting", "divide_and_conquer", "Return how many index pairs form an inversion.", "nums=[2,4,1,3,5]", "3"),
        ],
        "mcqs": [
            _mcq("searching-mcq-1", "What is the key promise of binary search?", ["You inspect every element once.", "Each comparison cuts away half of the remaining answer space.", "It uses no extra space.", "It only works on trees."], 1, "Binary search wins because it halves the candidate region."),
            _mcq("searching-mcq-2", "Why is merge sort often preferred for linked lists?", ["Because linked lists support random access.", "Because merging sequential nodes is natural and stable.", "Because merge sort uses no comparisons.", "Because quicksort cannot sort numbers."], 1, "Linked lists merge cleanly without costly random access."),
        ],
    },
    {
        "slug": "hashing",
        "title": "Hashing",
        "group": "Pattern Building",
        "subtopics": ["Direct lookup", "Frequency tables", "Prefix hashing", "Set-based reasoning"],
        "concept": """
            Hashing is the fastest way to turn "have I seen this state before?" into a constant-time
            question on average.
        """,
        "time_complexity": [
            "Lookup / insert: O(1) expected",
            "Frequency-map build: O(n)",
        ],
        "space_complexity": "Usually O(n) extra space to buy faster lookups.",
        "real_world_intuition": "It is the in-memory version of keeping an index card that jumps straight to what you need.",
        "alternative_approaches": [
            "Sorting when you want deterministic order too",
            "Arrays instead of maps when the key domain is tiny",
            "Prefix maps when the question is about ranges or subarrays",
        ],
        "interview_pitch": """
            Be explicit about what the hash key represents. Good hashing answers are really about
            choosing the right state to memoize.
        """,
        "visual_intuition": """
            key -> stored fact
        """,
        "implementations": _code(
            """
            def contains_duplicate(nums):
                seen = set()
                for value in nums:
                    if value in seen:
                        return True
                    seen.add(value)
                return False
            """,
            """
            bool containsDuplicate(const vector<int>& nums) {
                unordered_set<int> seen;
                for (int value : nums) {
                    if (seen.count(value)) return true;
                    seen.insert(value);
                }
                return false;
            }
            """,
            """
            boolean containsDuplicate(int[] nums) {
                Set<Integer> seen = new HashSet<>();
                for (int value : nums) {
                    if (seen.contains(value)) return true;
                    seen.add(value);
                }
                return false;
            }
            """,
        ),
        "practice_specs": [
            ("Contains Duplicate", "Easy", "Set membership", "hash_lookup", "Return true if any value appears at least twice.", "nums=[1,2,3,1]", "True"),
            ("Top K Frequent Elements", "Medium", "Frequency buckets", "frequency_count", "Return the k most frequent values.", "nums=[1,1,1,2,2,3], k=2", "[1,2]"),
            ("Longest Consecutive Sequence", "Medium", "Hash set expansion", "hash_lookup", "Return the length of the longest consecutive sequence.", "nums=[100,4,200,1,3,2]", "4"),
            ("Subarray Sum Equals K", "Medium", "Prefix hashing", "prefix_hash", "Return the number of subarrays whose sum equals k.", "nums=[1,1,1], k=2", "2"),
            ("Happy Number", "Easy", "Cycle detection via hashing", "hash_lookup", "Return true if repeatedly summing squared digits eventually reaches 1.", "n=19", "True"),
            ("Isomorphic Strings", "Easy", "Bidirectional mapping", "hash_lookup", "Return true if characters in s can be replaced to get t.", "s='egg', t='add'", "True"),
            ("4Sum II", "Medium", "Hash aggregation", "hash_lookup", "Count quadruples whose sum is zero.", "nums1=[1,2], nums2=[-2,-1], nums3=[-1,2], nums4=[0,2]", "2"),
            ("Valid Sudoku", "Medium", "Constraint hashing", "hash_lookup", "Return true if the partially filled Sudoku board is valid.", "board=9x9 puzzle", "True"),
            ("Ransom Note", "Easy", "Frequency maps", "frequency_count", "Return true if ransomNote can be built from magazine letters.", "ransomNote='aa', magazine='aab'", "True"),
            ("Find Duplicate File in System", "Medium", "Content hashing", "hash_lookup", "Group file paths that share the same content.", "paths=['root/a 1.txt(abcd) 2.txt(efgh)','root/c 3.txt(abcd)']", "[['root/a/1.txt','root/c/3.txt']]"),
        ],
        "mcqs": [
            _mcq("hashing-mcq-1", "What do you gain with hashing?", ["Guaranteed sorted order.", "Fast expected lookup for the chosen state.", "Lower memory usage than arrays.", "No collisions ever."], 1, "Hashing buys average O(1) access to previously stored state."),
            _mcq("hashing-mcq-2", "When should you prefer a fixed-size frequency array over a hash map?", ["When the key range is small and known.", "When you need recursion.", "When order matters most.", "When the data is already sorted."], 0, "A bounded domain is often faster and simpler than hashing."),
        ],
    },
    {
        "slug": "two_pointers_sliding_window",
        "title": "Two Pointers / Sliding Window",
        "group": "Pattern Building",
        "subtopics": ["Opposite-direction scans", "Same-direction windows", "Window counts", "Shrink/expand invariants"],
        "concept": """
            Two pointers and sliding windows are really about controlling a boundary. The whole
            trick is knowing exactly when the boundary should move and what it means when it does.
        """,
        "time_complexity": [
            "Most pointer scans: O(n)",
            "Window expansion/shrink: O(n)",
        ],
        "space_complexity": "Often O(1) to O(alphabet size), depending on the tracked state.",
        "real_world_intuition": "It is like maintaining the shortest stretch of a timeline that still contains everything you need.",
        "alternative_approaches": [
            "Sorting plus opposite pointers",
            "Hashing for direct lookup when order does not matter",
            "Deque when the window needs best-value maintenance",
        ],
        "interview_pitch": """
            Define the invariant of the active range. If the window is valid, say why. If it is
            invalid, say exactly which pointer movement repairs it.
        """,
        "visual_intuition": """
            left ---- right
        """,
        "implementations": _code(
            """
            def max_area(height):
                left, right = 0, len(height) - 1
                best = 0
                while left < right:
                    width = right - left
                    best = max(best, width * min(height[left], height[right]))
                    if height[left] < height[right]:
                        left += 1
                    else:
                        right -= 1
                return best
            """,
            """
            int maxArea(vector<int>& height) {
                int left = 0;
                int right = static_cast<int>(height.size()) - 1;
                int best = 0;
                while (left < right) {
                    int width = right - left;
                    best = max(best, width * min(height[left], height[right]));
                    if (height[left] < height[right]) left++;
                    else right--;
                }
                return best;
            }
            """,
            """
            int maxArea(int[] height) {
                int left = 0;
                int right = height.length - 1;
                int best = 0;
                while (left < right) {
                    int width = right - left;
                    best = Math.max(best, width * Math.min(height[left], height[right]));
                    if (height[left] < height[right]) left++;
                    else right--;
                }
                return best;
            }
            """,
        ),
        "practice_specs": [
            ("Two Sum II - Input Array Is Sorted", "Easy", "Opposite pointers", "two_pointer_scan", "Return the 1-indexed positions of the pair that adds to the target.", "numbers=[2,7,11,15], target=9", "[1, 2]"),
            ("3Sum", "Medium", "Sorted two pointers", "two_pointer_scan", "Return every unique triplet whose sum is zero.", "nums=[-1,0,1,2,-1,-4]", "[[-1,-1,2],[-1,0,1]]"),
            ("Move Zeroes", "Easy", "Same-direction pointers", "two_pointer_scan", "Move all zeroes to the end while preserving the order of non-zero values.", "nums=[0,1,0,3,12]", "[1,3,12,0,0]"),
            ("Longest Repeating Character Replacement", "Medium", "Sliding window", "sliding_window", "Return the longest substring that can be made uniform after at most k replacements.", "s='AABABBA', k=1", "4"),
            ("Minimum Size Subarray Sum", "Medium", "Shrinking window", "sliding_window", "Return the minimum length of a subarray whose sum is at least target.", "target=7, nums=[2,3,1,2,4,3]", "2"),
            ("Permutation in String", "Medium", "Window counts", "sliding_window", "Return true if s2 contains a permutation of s1.", "s1='ab', s2='eidbaooo'", "True"),
            ("Max Consecutive Ones III", "Medium", "Budgeted window", "sliding_window", "Return the longest subarray containing at most k zeroes.", "nums=[1,1,1,0,0,0,1,1,1,1,0], k=2", "6"),
            ("Longest Mountain in Array", "Medium", "Boundary scan", "two_pointer_scan", "Return the length of the longest mountain subarray.", "arr=[2,1,4,7,3,2,5]", "5"),
            ("Trapping Rain Water", "Hard", "Opposite pointers", "two_pointer_scan", "Return the total trapped rain water.", "height=[4,2,0,3,2,5]", "9"),
            ("Minimum Window Subsequence", "Hard", "Window scan", "sliding_window", "Return the shortest substring of s1 that contains s2 as a subsequence.", "s1='abcdebdde', s2='bde'", "'bcde'"),
        ],
        "mcqs": [
            _mcq("twopointers-mcq-1", "When does a two-pointer scan usually beat brute force?", ["When order or boundary movement lets you discard work permanently.", "When the input is recursive.", "When you need every permutation.", "When you are building a heap."], 0, "Pointers work because each move destroys impossible search space."),
            _mcq("twopointers-mcq-2", "What is the defining question of a sliding window problem?", ["How do I recurse?", "When is the current window valid or optimal enough to shrink?", "Can I sort the graph?", "Should I reverse the list?"], 1, "Window problems live or die on a precise validity condition."),
        ],
    },
    {
        "slug": "trees",
        "title": "Trees",
        "group": "Core Structures",
        "subtopics": ["DFS", "BFS", "BST rules", "Path aggregation"],
        "concept": """
            Tree problems become easier once you state what one recursive call means. The usual
            building blocks are DFS, BFS, in-order structure, and path-based aggregation.
        """,
        "time_complexity": [
            "Full traversal: O(n)",
            "Balanced BST search: O(log n)",
        ],
        "space_complexity": "O(h) recursion or queue space, where h is height for DFS and O(width) for BFS.",
        "real_world_intuition": "A tree is a hierarchy where every local decision splits into smaller, similar subproblems.",
        "alternative_approaches": [
            "DFS recursion for natural structural questions",
            "BFS for level-order output or shortest-edge distance",
            "In-order traversal when BST ordering matters",
        ],
        "interview_pitch": """
            Say whether your recursive function returns a value, updates external state, or both.
            That sentence usually organizes the whole solution.
        """,
        "visual_intuition": """
                8
              /   \
             3    10
        """,
        "implementations": _code(
            """
            def max_depth(root):
                if not root:
                    return 0
                return 1 + max(max_depth(root.left), max_depth(root.right))
            """,
            """
            int maxDepth(TreeNode* root) {
                if (!root) return 0;
                return 1 + max(maxDepth(root->left), maxDepth(root->right));
            }
            """,
            """
            int maxDepth(TreeNode root) {
                if (root == null) return 0;
                return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
            }
            """,
        ),
        "practice_specs": [
            ("Maximum Depth of Binary Tree", "Easy", "DFS", "tree_traversal", "Return the maximum depth of the tree.", "root=[3,9,20,null,null,15,7]", "3"),
            ("Same Tree", "Easy", "DFS", "tree_traversal", "Return true if two binary trees are structurally identical with equal values.", "p=[1,2,3], q=[1,2,3]", "True"),
            ("Invert Binary Tree", "Easy", "DFS", "tree_traversal", "Invert the binary tree in place.", "root=[4,2,7,1,3,6,9]", "[4,7,2,9,6,3,1]"),
            ("Binary Tree Level Order Traversal", "Medium", "BFS", "tree_traversal", "Return the values of the tree level by level.", "root=[3,9,20,null,null,15,7]", "[[3],[9,20],[15,7]]"),
            ("Validate Binary Search Tree", "Medium", "BST invariant", "bst_property", "Return true if the tree is a valid BST.", "root=[2,1,3]", "True"),
            ("Kth Smallest Element in a BST", "Medium", "In-order traversal", "bst_property", "Return the kth smallest key in the BST.", "root=[3,1,4,null,2], k=1", "1"),
            ("Lowest Common Ancestor of a Binary Search Tree", "Medium", "BST invariant", "bst_property", "Return the lowest common ancestor of two nodes in a BST.", "root=[6,2,8,0,4,7,9,null,null,3,5], p=2, q=8", "6"),
            ("Diameter of Binary Tree", "Medium", "Post-order aggregation", "tree_traversal", "Return the diameter measured in edges.", "root=[1,2,3,4,5]", "3"),
            ("Path Sum", "Easy", "Root-to-leaf DFS", "tree_traversal", "Return true if a root-to-leaf path sums to the target.", "root=[5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum=22", "True"),
            ("Serialize and Deserialize Binary Tree", "Hard", "Traversal encoding", "tree_traversal", "Design a serializer and deserializer for binary trees.", "root=[1,2,3,null,null,4,5]", "round-trips correctly"),
        ],
        "mcqs": [
            _mcq("trees-mcq-1", "What makes in-order traversal special for BSTs?", ["It always gives breadth-first order.", "It visits values in sorted order.", "It uses less memory than DFS.", "It works only on complete trees."], 1, "The BST left-root-right rule produces sorted output."),
            _mcq("trees-mcq-2", "What should a recursive tree helper usually define first?", ["The color palette.", "What one call returns or represents.", "The queue implementation.", "The hash function."], 1, "Tree recursion becomes manageable once one call has a precise meaning."),
        ],
    },
    {
        "slug": "heap_priority_queue",
        "title": "Heap / Priority Queue",
        "group": "Core Structures",
        "subtopics": ["Top-k selection", "Streaming medians", "K-way merge", "Scheduling"],
        "concept": """
            Heaps are for repeatedly asking "what is the current best candidate?" without fully
            sorting the entire dataset.
        """,
        "time_complexity": [
            "Push / pop: O(log n)",
            "Peek: O(1)",
        ],
        "space_complexity": "Usually O(k) to O(n), depending on how many candidates you keep active.",
        "real_world_intuition": "It is the interview version of a live leaderboard.",
        "alternative_approaches": [
            "Sorting when you need the entire order",
            "Quickselect for one offline order statistic",
            "Deque or queue when arrival order matters more than priority",
        ],
        "interview_pitch": """
            Say what "best" means in the heap. Is the top the smallest candidate, the largest
            candidate, or the next event by time?
        """,
        "visual_intuition": """
              top
               2
             /   \
            4     7
        """,
        "implementations": _code(
            """
            import heapq


            def kth_largest(nums, k):
                heap = nums[:k]
                heapq.heapify(heap)
                for value in nums[k:]:
                    if value > heap[0]:
                        heapq.heapreplace(heap, value)
                return heap[0]
            """,
            """
            int kthLargest(vector<int>& nums, int k) {
                priority_queue<int, vector<int>, greater<int>> heap;
                for (int value : nums) {
                    heap.push(value);
                    if (heap.size() > k) heap.pop();
                }
                return heap.top();
            }
            """,
            """
            int kthLargest(int[] nums, int k) {
                PriorityQueue<Integer> heap = new PriorityQueue<>();
                for (int value : nums) {
                    heap.offer(value);
                    if (heap.size() > k) heap.poll();
                }
                return heap.peek();
            }
            """,
        ),
        "practice_specs": [
            ("Kth Largest Element in an Array", "Easy", "Top-k selection", "heap_selection", "Return the kth largest element in the array.", "nums=[3,2,1,5,6,4], k=2", "5"),
            ("Top K Frequent Elements", "Medium", "Frequency heap", "heap_selection", "Return the k most frequent elements.", "nums=[1,1,1,2,2,3], k=2", "[1,2]"),
            ("Merge K Sorted Lists", "Hard", "K-way merge", "heap_selection", "Merge k sorted linked lists into one sorted list.", "lists=[[1,4,5],[1,3,4],[2,6]]", "[1,1,2,3,4,4,5,6]"),
            ("K Closest Points to Origin", "Medium", "Bounded heap", "heap_selection", "Return the k points nearest to the origin.", "points=[[1,3],[-2,2]], k=1", "[[-2,2]]"),
            ("Task Scheduler", "Medium", "Greedy scheduling", "heap_selection", "Return the least time needed to finish all tasks with cooldown.", "tasks=['A','A','A','B','B','B'], n=2", "8"),
            ("Find Median from Data Stream", "Hard", "Two heaps", "heap_selection", "Design a structure that returns the current median after each insertion.", "ops=['addNum','addNum','findMedian'], values=[[1],[2],[]]", "1.5"),
            ("Meeting Rooms II", "Medium", "End-time heap", "heap_selection", "Return the minimum number of meeting rooms required.", "intervals=[[0,30],[5,10],[15,20]]", "2"),
            ("Reorganize String", "Medium", "Frequency heap", "heap_selection", "Rearrange the string so no equal characters are adjacent, or return empty.", "s='aab'", "'aba'"),
            ("Last Stone Weight", "Easy", "Max heap", "heap_selection", "Repeatedly smash the two heaviest stones until at most one remains.", "stones=[2,7,4,1,8,1]", "1"),
            ("Smallest Range Covering Elements from K Lists", "Hard", "K-way merge", "heap_selection", "Return the smallest range that includes at least one number from every list.", "nums=[[4,10,15,24,26],[0,9,12,20],[5,18,22,30]]", "[20,24]"),
        ],
        "mcqs": [
            _mcq("heap-mcq-1", "Why is a heap better than fully sorting for streaming top-k?", ["It uses no comparisons.", "It keeps only the candidates that still matter.", "It guarantees O(1) updates.", "It always stores values in full sorted order."], 1, "A bounded heap avoids paying for a full global order."),
            _mcq("heap-mcq-2", "When should a priority queue beat a normal queue?", ["When arrival order defines correctness.", "When the next item should be chosen by score or priority.", "When you need recursion.", "When there are no duplicates."], 1, "Heaps are about best-candidate-first processing."),
        ],
    },
    {
        "slug": "graphs",
        "title": "Graphs",
        "group": "Core Structures",
        "subtopics": ["DFS/BFS", "Connectivity", "Shortest paths", "Topological reasoning"],
        "concept": """
            Graph questions start getting easier the moment you say what a node means and what an
            edge means. After that, most problems become traversal, connectivity, or shortest-path tasks.
        """,
        "time_complexity": [
            "DFS/BFS: O(V + E)",
            "Dijkstra with heap: O((V + E) log V)",
        ],
        "space_complexity": "Usually O(V + E) for adjacency structure plus visited state.",
        "real_world_intuition": "A graph is a map of relationships rather than a container of positions.",
        "alternative_approaches": [
            "DFS for deep structural exploration",
            "BFS for minimum-edge distance",
            "Union find for connectivity without full traversal",
        ],
        "interview_pitch": """
            Define the graph aloud. "Nodes are courses, edges are prerequisites." That sentence
            often solves half the problem before code is written.
        """,
        "visual_intuition": """
            A -> B -> D
            |    ^
            v    |
            C ----
        """,
        "implementations": _code(
            """
            def dfs(graph, start, seen=None):
                if seen is None:
                    seen = set()
                if start in seen:
                    return
                seen.add(start)
                for neighbor in graph[start]:
                    dfs(graph, neighbor, seen)
                return seen
            """,
            """
            void dfs(unordered_map<int, vector<int>>& graph, int start, unordered_set<int>& seen) {
                if (seen.count(start)) return;
                seen.insert(start);
                for (int neighbor : graph[start]) dfs(graph, neighbor, seen);
            }
            """,
            """
            void dfs(Map<Integer, List<Integer>> graph, int start, Set<Integer> seen) {
                if (seen.contains(start)) return;
                seen.add(start);
                for (int neighbor : graph.get(start)) dfs(graph, neighbor, seen);
            }
            """,
        ),
        "practice_specs": [
            ("Number of Islands", "Easy", "Grid connectivity", "graph_traversal", "Count the number of island components in a binary grid.", "grid=[['1','1','0'],['0','1','0'],['1','0','1']]", "3"),
            ("Clone Graph", "Medium", "Traversal with memo", "graph_traversal", "Create a deep copy of the graph.", "graph=1-2-3-4 cycle", "deep copy"),
            ("Course Schedule", "Medium", "Cycle detection", "topological_sort", "Return true if all courses can be finished.", "numCourses=2, prerequisites=[[1,0]]", "True"),
            ("Pacific Atlantic Water Flow", "Medium", "Reachability", "graph_traversal", "Return all grid cells that can reach both oceans.", "heights=[[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],[6,7,1,4,5],[5,1,1,2,4]]", "reachable cells"),
            ("Network Delay Time", "Medium", "Shortest path", "dijkstra", "Return the time for all nodes to receive the signal.", "times=[[2,1,1],[2,3,1],[3,4,1]], n=4, k=2", "2"),
            ("Word Ladder", "Hard", "State BFS", "graph_traversal", "Return the minimum number of transformations from beginWord to endWord.", "beginWord='hit', endWord='cog', wordList=['hot','dot','dog','lot','log','cog']", "5"),
            ("Accounts Merge", "Medium", "Connectivity", "graph_traversal", "Merge account lists that share any email address.", "accounts=[['John','johnsmith@mail.com','john_newyork@mail.com'],['John','johnsmith@mail.com','john00@mail.com']]", "merged accounts"),
            ("Surrounded Regions", "Medium", "Boundary BFS/DFS", "graph_traversal", "Flip every captured region of O cells.", "board=[['X','X','X','X'],['X','O','O','X'],['X','X','O','X'],['X','O','X','X']]", "captured board"),
            ("Cheapest Flights Within K Stops", "Medium", "Shortest path with state", "dijkstra", "Return the cheapest flight cost with at most k stops.", "n=4, flights=[[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]], src=0, dst=3, k=1", "700"),
            ("Number of Connected Components in an Undirected Graph", "Medium", "Component counting", "graph_traversal", "Return how many connected components the graph contains.", "n=5, edges=[[0,1],[1,2],[3,4]]", "2"),
        ],
        "mcqs": [
            _mcq("graphs-mcq-1", "What does O(V + E) mean for graph traversal?", ["Every edge is processed for every vertex.", "Each vertex and edge is explored only a constant number of times overall.", "Only vertices matter.", "Traversal is always quadratic."], 1, "Adjacency-list traversal is linear in the size of the graph representation."),
            _mcq("graphs-mcq-2", "What does a directed cycle mean in Course Schedule?", ["The answer is always one.", "The prerequisite structure is impossible to complete.", "Every course is optional.", "You should use Dijkstra."], 1, "A directed cycle means the dependencies can never be resolved."),
        ],
    },
    {
        "slug": "dynamic_programming",
        "title": "Dynamic Programming",
        "group": "Advanced Reasoning",
        "subtopics": ["Linear DP", "Sequence DP", "Grid DP", "Subset DP"],
        "concept": """
            Dynamic programming is about reusing the answer to smaller states instead of solving
            the same subproblem repeatedly.
        """,
        "time_complexity": [
            "Number of states times transition cost",
            "Can often be reduced with rolling arrays or monotonic observations",
        ],
        "space_complexity": "Depends on the state table. Many 1D DPs compress to O(1) or O(n).",
        "real_world_intuition": "It is like keeping a notebook of the best result for every partial milestone so you never recompute it.",
        "alternative_approaches": [
            "Memoized DFS for naturally recursive states",
            "Tabulation for clearer dependency ordering",
            "Greedy only when a local-choice proof exists",
        ],
        "interview_pitch": """
            Start with the state sentence. "dp[i] is the best answer using the first i items." Once
            that sentence is good, the recurrence is usually nearby.
        """,
        "visual_intuition": """
            solve(n) -> smaller states reused
        """,
        "implementations": _code(
            """
            def climb_stairs(n):
                if n <= 2:
                    return n
                prev2, prev1 = 1, 2
                for _ in range(3, n + 1):
                    prev2, prev1 = prev1, prev1 + prev2
                return prev1
            """,
            """
            int climbStairs(int n) {
                if (n <= 2) return n;
                int prev2 = 1;
                int prev1 = 2;
                for (int step = 3; step <= n; ++step) {
                    int current = prev1 + prev2;
                    prev2 = prev1;
                    prev1 = current;
                }
                return prev1;
            }
            """,
            """
            int climbStairs(int n) {
                if (n <= 2) return n;
                int prev2 = 1;
                int prev1 = 2;
                for (int step = 3; step <= n; step++) {
                    int current = prev1 + prev2;
                    prev2 = prev1;
                    prev1 = current;
                }
                return prev1;
            }
            """,
        ),
        "practice_specs": [
            ("Climbing Stairs", "Easy", "Linear DP", "dp_linear", "Return how many ways there are to climb n stairs taking 1 or 2 steps.", "n=5", "8"),
            ("House Robber", "Medium", "Linear DP", "dp_linear", "Return the maximum value that can be robbed without taking adjacent houses.", "nums=[2,7,9,3,1]", "12"),
            ("Coin Change", "Medium", "Unbounded DP", "dp_subset", "Return the minimum number of coins needed to make the target amount.", "coins=[1,2,5], amount=11", "3"),
            ("Unique Paths", "Medium", "Grid DP", "dp_linear", "Return the number of unique paths from the top-left to the bottom-right of the grid.", "m=3, n=7", "28"),
            ("Longest Increasing Subsequence", "Medium", "Sequence DP", "dp_sequence", "Return the length of the longest strictly increasing subsequence.", "nums=[10,9,2,5,3,7,101,18]", "4"),
            ("Longest Common Subsequence", "Medium", "Sequence DP", "dp_sequence", "Return the length of the LCS of two strings.", "text1='abcde', text2='ace'", "3"),
            ("Decode Ways", "Medium", "Linear DP", "dp_linear", "Return how many ways the digit string can be decoded.", "s='226'", "3"),
            ("Partition Equal Subset Sum", "Medium", "Subset DP", "dp_subset", "Return true if the array can be split into two equal-sum subsets.", "nums=[1,5,11,5]", "True"),
            ("Edit Distance", "Hard", "Sequence DP", "dp_sequence", "Return the minimum number of edits needed to transform one string into another.", "word1='horse', word2='ros'", "3"),
            ("Target Sum", "Medium", "Subset DP", "dp_subset", "Count how many ways to assign + or - signs to reach the target.", "nums=[1,1,1,1,1], target=3", "5"),
        ],
        "mcqs": [
            _mcq("dp-mcq-1", "What makes a problem a good DP candidate?", ["It uses a graph.", "It has overlapping subproblems and reusable states.", "It needs sorting.", "It always has a greedy solution."], 1, "DP is about repeated smaller states and a recurrence that combines them."),
            _mcq("dp-mcq-2", "Why do many linear DPs compress to O(1) space?", ["Because the answer never changes.", "Because each new state depends on only a small fixed number of earlier states.", "Because recursion disappears.", "Because arrays are faster than maps."], 1, "If only the last few states matter, the full table is unnecessary."),
        ],
    },
    {
        "slug": "greedy_algorithms",
        "title": "Greedy Algorithms",
        "group": "Advanced Reasoning",
        "subtopics": ["Frontier tracking", "Interval choices", "Scheduling", "Local proofs"],
        "concept": """
            Greedy algorithms work when a locally optimal choice can be proven to never hurt the
            final answer. The proof matters just as much as the implementation.
        """,
        "time_complexity": [
            "Often O(n) after sorting or scanning",
            "Interval variants are frequently O(n log n) due to sorting",
        ],
        "space_complexity": "Commonly O(1) extra after sorting, though some scheduling variants use heaps.",
        "real_world_intuition": "Greedy is choosing the best move now because you can prove future-you will not regret it.",
        "alternative_approaches": [
            "Dynamic programming when the local choice cannot be proven",
            "Sorting before greedy selection for interval tasks",
            "Heaps for time-ordered scheduling",
        ],
        "interview_pitch": """
            Never stop at the implementation. Say why the local choice preserves or maximizes future
            flexibility. That proof is the heart of a greedy answer.
        """,
        "visual_intuition": """
            keep the best frontier or earliest ending boundary
        """,
        "implementations": _code(
            """
            def can_jump(nums):
                reach = 0
                for index, jump in enumerate(nums):
                    if index > reach:
                        return False
                    reach = max(reach, index + jump)
                return True
            """,
            """
            bool canJump(vector<int>& nums) {
                int reach = 0;
                for (int index = 0; index < nums.size(); ++index) {
                    if (index > reach) return false;
                    reach = max(reach, index + nums[index]);
                }
                return true;
            }
            """,
            """
            boolean canJump(int[] nums) {
                int reach = 0;
                for (int index = 0; index < nums.length; index++) {
                    if (index > reach) return false;
                    reach = Math.max(reach, index + nums[index]);
                }
                return true;
            }
            """,
        ),
        "practice_specs": [
            ("Jump Game", "Medium", "Reach frontier", "greedy_reach", "Return true if the last index is reachable.", "nums=[2,3,1,1,4]", "True"),
            ("Jump Game II", "Medium", "Layered greedy", "greedy_reach", "Return the minimum number of jumps needed to reach the end.", "nums=[2,3,1,1,4]", "2"),
            ("Gas Station", "Medium", "Running balance", "greedy_reach", "Return the start index that lets you complete the circular route.", "gas=[1,2,3,4,5], cost=[3,4,5,1,2]", "3"),
            ("Non-overlapping Intervals", "Medium", "Interval greedy", "greedy_interval", "Return the minimum number of intervals to erase to remove all overlaps.", "intervals=[[1,2],[2,3],[3,4],[1,3]]", "1"),
            ("Partition Labels", "Medium", "Greedy boundaries", "greedy_interval", "Partition the string so each letter appears in at most one part.", "s='ababcbacadefegdehijhklij'", "[9,7,8]"),
            ("Assign Cookies", "Easy", "Sorted greedy", "greedy_interval", "Return the maximum number of satisfied children.", "g=[1,2,3], s=[1,1]", "1"),
            ("Lemonade Change", "Easy", "Local cash state", "greedy_reach", "Return true if you can provide correct change to every customer.", "bills=[5,5,5,10,20]", "True"),
            ("Minimum Number of Arrows to Burst Balloons", "Medium", "Interval greedy", "greedy_interval", "Return the minimum arrows needed to burst every balloon interval.", "points=[[10,16],[2,8],[1,6],[7,12]]", "2"),
            ("Candy", "Hard", "Bidirectional greedy", "greedy_interval", "Distribute candy so higher-rated children get more than their neighbors.", "ratings=[1,0,2]", "5"),
            ("Meeting Rooms II", "Medium", "Scheduling", "heap_selection", "Return the minimum meeting rooms required.", "intervals=[[0,30],[5,10],[15,20]]", "2"),
        ],
        "mcqs": [
            _mcq("greedy-mcq-1", "What must be true before a greedy solution is trustworthy?", ["The input is sorted.", "A local choice can be proven safe for the global objective.", "The graph is acyclic.", "There are no duplicates."], 1, "Greedy needs a proof that local optimality does not damage the final answer."),
            _mcq("greedy-mcq-2", "Why do interval greedy problems often sort by end time?", ["Because end times are always smaller.", "Because choosing the earliest finishing interval leaves maximum room for the future.", "Because arrays require sorting.", "Because heaps cannot store intervals."], 1, "Earliest finish preserves as much future space as possible."),
        ],
    },
    {
        "slug": "bit_manipulation",
        "title": "Bit Manipulation",
        "group": "Advanced Reasoning",
        "subtopics": ["XOR identities", "Bit counting", "Masks", "Range tricks"],
        "concept": """
            Bit manipulation questions reward comfort with binary identities. A one-line bit trick
            is only impressive if you can explain why it works.
        """,
        "time_complexity": [
            "Per-bit operations: O(number of bits)",
            "Mask enumeration: O(2^n * n) for subset generation",
        ],
        "space_complexity": "Often O(1) extra space for pure bit tricks.",
        "real_world_intuition": "Bits are tiny yes/no switches that let you encode many choices compactly.",
        "alternative_approaches": [
            "Hashing when the bit trick is not obvious",
            "DP when counting over bit states",
            "Math identities when the number pattern is simpler than the bits",
        ],
        "interview_pitch": """
            Never just cite the trick. Explain the identity: why XOR cancels, why n & (n - 1)
            clears the lowest set bit, or why the mask represents a subset.
        """,
        "visual_intuition": """
            mask 1011 -> choose items 0, 1, and 3
        """,
        "implementations": _code(
            """
            def single_number(nums):
                answer = 0
                for value in nums:
                    answer ^= value
                return answer
            """,
            """
            int singleNumber(vector<int>& nums) {
                int answer = 0;
                for (int value : nums) answer ^= value;
                return answer;
            }
            """,
            """
            int singleNumber(int[] nums) {
                int answer = 0;
                for (int value : nums) answer ^= value;
                return answer;
            }
            """,
        ),
        "practice_specs": [
            ("Single Number", "Easy", "XOR cancellation", "bit_xor", "Return the element that appears once when every other element appears twice.", "nums=[4,1,2,1,2]", "4"),
            ("Counting Bits", "Easy", "Bit DP", "bit_count", "Return the number of set bits for every integer from 0 to n.", "n=5", "[0,1,1,2,1,2]"),
            ("Number of 1 Bits", "Easy", "Bit counting", "bit_count", "Return the number of set bits in the binary representation of the input.", "n=11", "3"),
            ("Reverse Bits", "Easy", "Bit shifts", "bit_count", "Reverse the bits of a 32-bit unsigned integer.", "n=43261596", "964176192"),
            ("Missing Number", "Easy", "XOR cancellation", "bit_xor", "Return the missing value from the range [0, n].", "nums=[9,6,4,2,3,5,7,0,1]", "8"),
            ("Sum of Two Integers", "Medium", "Bit carry simulation", "bit_xor", "Return the sum of two integers without using + or -.", "a=1, b=2", "3"),
            ("Subsets", "Medium", "Bitmask enumeration", "bitmask_enumeration", "Generate every subset using a bitmask representation.", "nums=[1,2,3]", "all subsets"),
            ("Bitwise AND of Numbers Range", "Medium", "Common prefix", "bit_count", "Return the bitwise AND of every number in the inclusive range.", "left=5, right=7", "4"),
            ("Power of Two", "Easy", "Single-bit property", "bit_count", "Return true if n is a power of two.", "n=16", "True"),
            ("Maximum XOR of Two Numbers in an Array", "Hard", "Bitwise greedy", "bit_xor", "Return the maximum XOR obtainable from any pair of values.", "nums=[3,10,5,25,2,8]", "28"),
        ],
        "mcqs": [
            _mcq("bits-mcq-1", "Why does XOR solve Single Number?", ["Because XOR sorts the array.", "Because pairs cancel out and zero is the neutral element.", "Because XOR is always larger.", "Because XOR counts bits."], 1, "x ^ x = 0 and x ^ 0 = x are the key identities."),
            _mcq("bits-mcq-2", "What does n & (n - 1) do?", ["Adds one to n.", "Clears the lowest set bit.", "Reverses all bits.", "Finds the highest set bit."], 1, "That trick is the workhorse of many bit-counting solutions."),
        ],
    },
]


IMPORTANT_PRACTICE_ADDITIONS = {
    "arrays": [
        ("Maximum Product Subarray", "Medium", "Kadane variant", "kadane", "Return the maximum product of a contiguous subarray.", "nums=[2,3,-2,4]", "6"),
        ("Subarray Sum Equals K", "Medium", "Prefix sums + hashing", "prefix_hash", "Return the count of subarrays whose sum equals k.", "nums=[1,2,3], k=3", "2"),
        ("Spiral Matrix", "Medium", "Boundary traversal", "matrix_marking", "Return all matrix elements in spiral order.", "matrix=[[1,2,3],[4,5,6],[7,8,9]]", "[1,2,3,6,9,8,7,4,5]"),
        ("Majority Element", "Easy", "Frequency / voting insight", "frequency_count", "Return the element that appears more than n / 2 times.", "nums=[2,2,1,1,1,2,2]", "2"),
        ("Find Minimum in Rotated Sorted Array", "Medium", "Binary search", "binary_search", "Return the minimum element in a rotated sorted array.", "nums=[3,4,5,1,2]", "1"),
    ],
    "strings": [
        ("Palindromic Substrings", "Medium", "Center expansion", "center_expand", "Return the number of palindromic substrings in the input string.", "s='aaa'", "6"),
        ("Longest Common Prefix", "Easy", "Prefix scan", "running_best", "Return the longest common prefix shared by all strings.", "strs=['flower','flow','flight']", "'fl'"),
        ("Word Pattern", "Easy", "Bidirectional mapping", "hash_lookup", "Return true if the string follows the given pattern.", "pattern='abba', s='dog cat cat dog'", "True"),
        ("Reverse Words in a String", "Medium", "Two-pointer cleanup", "two_pointer_scan", "Reverse the order of words in the string and trim extra spaces.", "s='  hello world  '", "'world hello'"),
        ("Valid Parenthesis String", "Medium", "Wildcard parsing", "stack_parser", "Return true if every '*' can act as '(', ')' or empty so the string becomes valid.", "s='(*)'", "True"),
    ],
    "linked_list": [
        ("Middle of the Linked List", "Easy", "Fast and slow", "fast_slow", "Return the middle node of the linked list.", "head=[1,2,3,4,5]", "[3,4,5]"),
        ("Intersection of Two Linked Lists", "Easy", "Pointer alignment", "fast_slow", "Return the intersection node of two singly linked lists, or null if they do not intersect.", "listA=[4,1,8,4,5], listB=[5,6,1,8,4,5], skipA=2, skipB=3", "8"),
        ("Swap Nodes in Pairs", "Medium", "Local pointer rewiring", "list_merge", "Swap every two adjacent nodes and return the new head.", "head=[1,2,3,4]", "[2,1,4,3]"),
        ("Odd Even Linked List", "Medium", "Stable re-linking", "list_merge", "Group all odd-index nodes followed by even-index nodes.", "head=[1,2,3,4,5]", "[1,3,5,2,4]"),
        ("Rotate List", "Medium", "Tail reconnection", "reorder_weave", "Rotate the linked list to the right by k places.", "head=[1,2,3,4,5], k=2", "[4,5,1,2,3]"),
    ],
    "stack": [
        ("Next Greater Element I", "Easy", "Monotonic stack", "monotonic_stack", "Return the next greater element for every value in nums1 using nums2 as the reference order.", "nums1=[4,1,2], nums2=[1,3,4,2]", "[-1,3,-1]"),
        ("Online Stock Span", "Medium", "Monotonic stack", "monotonic_stack", "For each stock price, return the span of consecutive days with price less than or equal to today's price.", "prices=[100,80,60,70,60,75,85]", "[1,1,1,2,1,4,6]"),
        ("Car Fleet", "Medium", "Monotonic stack", "monotonic_stack", "Return how many car fleets reach the target.", "target=12, position=[10,8,0,5,3], speed=[2,4,1,1,3]", "3"),
        ("Score of Parentheses", "Medium", "Nested parsing", "stack_parser", "Return the score of a balanced parentheses string.", "s='(()(()))'", "6"),
        ("Remove All Adjacent Duplicates In String", "Easy", "String stack", "stack_parser", "Remove adjacent duplicate pairs repeatedly until none remain.", "s='abbaca'", "'ca'"),
    ],
    "queue": [
        ("Moving Average from Data Stream", "Easy", "Streaming queue", "queue_with_stacks", "Design a moving average class that returns the average of the last size values.", "size=3, values=[1,10,3,5]", "[1.0,5.5,4.67,6.0]"),
        ("Dota2 Senate", "Medium", "Round simulation", "queue_with_stacks", "Predict which party wins the senate voting game.", "senate='RDD'", "'Dire'"),
        ("Shortest Bridge", "Medium", "Bridge expansion", "bfs_grid", "Return the minimum number of 0s that must be flipped to connect the two islands.", "grid=[[0,1],[1,0]]", "1"),
        ("Snakes and Ladders", "Medium", "Board BFS", "graph_bfs", "Return the minimum moves needed to reach the final square on the board.", "board=[[-1,-1,-1],[-1,9,8],[-1,8,9]]", "1"),
        ("Number of Students Unable to Eat Lunch", "Easy", "Queue simulation", "queue_with_stacks", "Return how many students are unable to eat lunch under the sandwich order rules.", "students=[1,1,0,0], sandwiches=[0,1,0,1]", "0"),
    ],
    "recursion_backtracking": [
        ("Combination Sum II", "Medium", "Duplicate-aware search", "backtracking_constraint", "Return all unique combinations that sum to the target when each candidate can be used at most once.", "candidates=[10,1,2,7,6,1,5], target=8", "[[1,1,6],[1,2,5],[1,7],[2,6]]"),
        ("Subsets II", "Medium", "Duplicate-aware subsets", "backtracking_constraint", "Return all possible subsets without duplicate subsets.", "nums=[1,2,2]", "[[],[1],[2],[1,2],[2,2],[1,2,2]]"),
        ("Combination Sum III", "Medium", "Bounded choice search", "backtracking_constraint", "Return all valid combinations of k numbers that sum to n using numbers 1 through 9.", "k=3, n=7", "[[1,2,4]]"),
        ("Beautiful Arrangement", "Medium", "Position constraints", "backtracking_constraint", "Count the number of beautiful arrangements that can be built from 1 to n.", "n=2", "2"),
        ("Word Search II", "Hard", "Trie-style board search", "backtracking_constraint", "Return every word from the list that can be formed in the board.", "board=[['o','a','a','n'],['e','t','a','e'],['i','h','k','r'],['i','f','l','v']], words=['oath','pea','eat','rain']", "['oath','eat']"),
    ],
    "searching_sorting": [
        ("Search Insert Position", "Easy", "Boundary binary search", "binary_search", "Return the index where target is found or should be inserted in order.", "nums=[1,3,5,6], target=2", "1"),
        ("Search a 2D Matrix", "Medium", "Binary search", "binary_search", "Return true if the target exists in the sorted 2D matrix.", "matrix=[[1,3,5,7],[10,11,16,20],[23,30,34,60]], target=3", "True"),
        ("Find Minimum in Rotated Sorted Array", "Medium", "Binary search", "binary_search", "Return the minimum element in a rotated sorted array.", "nums=[4,5,6,7,0,1,2]", "0"),
        ("Koko Eating Bananas", "Medium", "Binary search on answer", "binary_search", "Return the minimum eating speed that lets Koko finish within h hours.", "piles=[3,6,7,11], h=8", "4"),
        ("Merge Sorted Array", "Easy", "Two-pointer merge", "two_pointer_scan", "Merge nums2 into nums1 as one sorted array in place.", "nums1=[1,2,3,0,0,0], m=3, nums2=[2,5,6], n=3", "[1,2,2,3,5,6]"),
    ],
    "hashing": [
        ("First Unique Character in a String", "Easy", "Frequency map", "frequency_count", "Return the index of the first non-repeating character.", "s='leetcode'", "0"),
        ("Find the Difference", "Easy", "Frequency map", "frequency_count", "Return the extra character added to t.", "s='abcd', t='abcde'", "'e'"),
        ("Intersection of Two Arrays", "Easy", "Set lookup", "hash_lookup", "Return the unique intersection of two arrays.", "nums1=[1,2,2,1], nums2=[2,2]", "[2]"),
        ("Continuous Subarray Sum", "Medium", "Prefix remainder hashing", "prefix_hash", "Return true if the array contains a size-at-least-two subarray whose sum is a multiple of k.", "nums=[23,2,4,6,7], k=6", "True"),
        ("Find All Duplicates in an Array", "Medium", "Seen-state detection", "hash_lookup", "Return every value that appears exactly twice.", "nums=[4,3,2,7,8,2,3,1]", "[2,3]"),
    ],
    "two_pointers_sliding_window": [
        ("Valid Palindrome II", "Easy", "One mismatch scan", "two_pointer_scan", "Return true if the string can be a palindrome after deleting at most one character.", "s='abca'", "True"),
        ("Backspace String Compare", "Easy", "Reverse two-pointer scan", "two_pointer_scan", "Return true if two strings are equal after applying backspaces.", "s='ab#c', t='ad#c'", "True"),
        ("Fruits Into Baskets", "Medium", "Bounded sliding window", "sliding_window", "Return the length of the longest subarray containing at most two distinct values.", "fruits=[1,2,1]", "3"),
        ("Longest Subarray of 1's After Deleting One Element", "Medium", "Budgeted window", "sliding_window", "Return the longest subarray of 1s obtainable after deleting one element.", "nums=[1,1,0,1]", "3"),
        ("Interval List Intersections", "Medium", "Parallel scan", "two_pointer_scan", "Return the intersections between two disjoint sorted interval lists.", "firstList=[[0,2],[5,10],[13,23],[24,25]], secondList=[[1,5],[8,12],[15,24],[25,26]]", "[[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]]"),
    ],
    "trees": [
        ("Balanced Binary Tree", "Easy", "Height check", "tree_traversal", "Return true if the height difference of every node is at most one.", "root=[3,9,20,null,null,15,7]", "True"),
        ("Subtree of Another Tree", "Easy", "Structural comparison", "tree_traversal", "Return true if subRoot appears as a subtree of root.", "root=[3,4,5,1,2], subRoot=[4,1,2]", "True"),
        ("Binary Tree Right Side View", "Medium", "Level traversal", "tree_traversal", "Return the values visible from the right side of the tree.", "root=[1,2,3,null,5,null,4]", "[1,3,4]"),
        ("Construct Binary Tree from Preorder and Inorder Traversal", "Medium", "Recursive partitioning", "divide_and_conquer", "Rebuild the binary tree from preorder and inorder traversal arrays.", "preorder=[3,9,20,15,7], inorder=[9,3,15,20,7]", "tree rebuilt"),
        ("Binary Tree Maximum Path Sum", "Hard", "Post-order aggregation", "tree_traversal", "Return the maximum path sum of any path in the binary tree.", "root=[-10,9,20,null,null,15,7]", "42"),
    ],
    "heap_priority_queue": [
        ("Kth Largest Element in a Stream", "Easy", "Streaming heap", "heap_selection", "Design a class that returns the kth largest value after each insertion.", "k=3, nums=[4,5,8,2], adds=[3,5,10,9,4]", "[4,5,5,8,8]"),
        ("Furthest Building You Can Reach", "Medium", "Resource heap", "heap_selection", "Return the furthest building index you can reach using bricks and ladders optimally.", "heights=[4,2,7,6,9,14,12], bricks=5, ladders=1", "4"),
        ("Find K Pairs with Smallest Sums", "Medium", "K-way heap expansion", "heap_selection", "Return the k pairs with the smallest sums from two sorted arrays.", "nums1=[1,7,11], nums2=[2,4,6], k=3", "[[1,2],[1,4],[1,6]]"),
        ("IPO", "Hard", "Capital-constrained selection", "heap_selection", "Return the maximum capital after completing at most k projects.", "k=2, w=0, profits=[1,2,3], capital=[0,1,1]", "4"),
        ("Sort Characters By Frequency", "Medium", "Frequency heap", "heap_selection", "Return the characters of the string sorted by descending frequency.", "s='tree'", "'eert'"),
    ],
    "graphs": [
        ("Find if Path Exists in Graph", "Easy", "Connectivity BFS", "graph_bfs", "Return true if there is a valid path between source and destination.", "n=3, edges=[[0,1],[1,2],[2,0]], source=0, destination=2", "True"),
        ("Is Graph Bipartite?", "Medium", "Two-color traversal", "graph_traversal", "Return true if the graph can be colored using two colors without conflicts.", "graph=[[1,3],[0,2],[1,3],[0,2]]", "True"),
        ("Minimum Height Trees", "Medium", "Layer trimming", "graph_bfs", "Return all roots of minimum-height trees.", "n=4, edges=[[1,0],[1,2],[1,3]]", "[1]"),
        ("Alien Dictionary", "Hard", "Topological order", "topological_sort", "Return a valid character order from the sorted alien dictionary words.", "words=['wrt','wrf','er','ett','rftt']", "'wertf'"),
        ("Redundant Connection", "Medium", "Cycle edge detection", "graph_traversal", "Return the edge that can be removed so the graph becomes a tree again.", "edges=[[1,2],[1,3],[2,3]]", "[2,3]"),
    ],
    "dynamic_programming": [
        ("Min Cost Climbing Stairs", "Easy", "Linear DP", "dp_linear", "Return the minimum cost to reach the top of the staircase.", "cost=[10,15,20]", "15"),
        ("House Robber II", "Medium", "Circular linear DP", "dp_linear", "Return the maximum value that can be robbed from a circular street.", "nums=[2,3,2]", "3"),
        ("Word Break", "Medium", "Prefix DP", "dp_subset", "Return true if the string can be segmented into dictionary words.", "s='leetcode', wordDict=['leet','code']", "True"),
        ("Best Time to Buy and Sell Stock with Cooldown", "Medium", "State DP", "dp_linear", "Return the maximum profit with as many transactions as you like and a one-day cooldown after selling.", "prices=[1,2,3,0,2]", "3"),
        ("Distinct Subsequences", "Hard", "Sequence DP", "dp_sequence", "Return how many distinct subsequences of s equal t.", "s='rabbbit', t='rabbit'", "3"),
    ],
    "greedy_algorithms": [
        ("Can Place Flowers", "Easy", "Local placement check", "greedy_reach", "Return true if n new flowers can be planted without adjacent flowers.", "flowerbed=[1,0,0,0,1], n=1", "True"),
        ("Wiggle Subsequence", "Medium", "Sign-change greedy", "greedy_reach", "Return the length of the longest wiggle subsequence.", "nums=[1,7,4,9,2,5]", "6"),
        ("Insert Interval", "Medium", "Interval merge choice", "greedy_interval", "Insert and merge the new interval into the sorted non-overlapping interval list.", "intervals=[[1,3],[6,9]], newInterval=[2,5]", "[[1,5],[6,9]]"),
        ("Queue Reconstruction by Height", "Medium", "Greedy ordering", "greedy_interval", "Reconstruct the queue based on height and in-front counts.", "people=[[7,0],[4,4],[7,1],[5,0],[6,1],[5,2]]", "[[5,0],[7,0],[5,2],[6,1],[4,4],[7,1]]"),
        ("Remove Duplicate Letters", "Medium", "Greedy stack", "monotonic_stack", "Return the smallest lexicographic string containing each letter exactly once.", "s='cbacdcbc'", "'acdb'"),
    ],
    "bit_manipulation": [
        ("Single Number II", "Medium", "Bit frequency", "bit_count", "Return the element that appears once when every other element appears three times.", "nums=[2,2,3,2]", "3"),
        ("Gray Code", "Medium", "Bit construction", "bitmask_enumeration", "Return a gray code sequence of n bits.", "n=2", "[0,1,3,2]"),
        ("Divide Two Integers", "Medium", "Shift subtraction", "bit_count", "Return the quotient of dividend divided by divisor without using multiplication, division, or mod.", "dividend=10, divisor=3", "3"),
        ("Maximum Product of Word Lengths", "Medium", "Mask comparison", "bitmask_enumeration", "Return the maximum product of lengths of two words that share no common letters.", "words=['abcw','baz','foo','bar','xtfn','abcdef']", "16"),
        ("Single Number III", "Medium", "Partition by differing bit", "bit_xor", "Return the two elements that appear once when every other element appears twice.", "nums=[1,2,1,3,2,5]", "[3,5]"),
    ],
}


def _build_topic(spec: dict) -> dict:
    practice_specs = list(spec["practice_specs"]) + IMPORTANT_PRACTICE_ADDITIONS.get(spec["slug"], [])
    unique_specs = []
    seen_titles = set()
    for row in practice_specs:
        if row[0] in seen_titles:
            continue
        seen_titles.add(row[0])
        unique_specs.append(row)
    practice = [
        _problem(
            spec["slug"],
            title,
            difficulty,
            subtopic,
            pattern_name,
            statement,
            example_input,
            example_output,
        )
        for title, difficulty, subtopic, pattern_name, statement, example_input, example_output in unique_specs
    ]
    return {
        "slug": spec["slug"],
        "title": spec["title"],
        "group": spec["group"],
        "subtopics": spec["subtopics"],
        "concept": _text(spec["concept"]),
        "time_complexity": spec["time_complexity"],
        "space_complexity": spec["space_complexity"],
        "real_world_intuition": _text(spec["real_world_intuition"]),
        "alternative_approaches": spec["alternative_approaches"],
        "interview_pitch": _text(spec["interview_pitch"]),
        "visual_intuition": _text(spec["visual_intuition"]),
        "implementations": spec["implementations"],
        "practice": practice,
        "mcqs": spec["mcqs"],
    }


TOPICS = [_build_topic(spec) for spec in TOPIC_SPECS]
TOPIC_MAP = {topic["slug"]: topic for topic in TOPICS}
