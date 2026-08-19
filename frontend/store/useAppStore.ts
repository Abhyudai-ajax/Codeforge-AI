import { create } from 'zustand';

export interface ProblemItem {
  id: string;
  slug: string;
  title: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  category: string;
  acceptance_rate: number;
  description_md?: string;
  starter_code?: Record<string, string>;
  test_cases?: Array<{ input: any; expected_output: any; is_sample?: boolean }>;
  constraints?: string[];
}

export interface WorkspaceFile {
  id: string;
  path: string;
  name: string;
  content: string;
  is_directory: boolean;
  language: string;
}

export interface AIMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface TestResultItem {
  test_case: number;
  input: any;
  expected_output: any;
  actual_output: string;
  passed: boolean;
  runtime_ms: number;
  error_message?: string;
}

export interface ExecutionResult {
  status: string;
  passed_test_cases: number;
  total_test_cases: number;
  runtime_ms: number;
  memory_mb: number;
  test_results: TestResultItem[];
}

interface AppState {
  // Navigation
  activeView: 'vscode' | 'leetcode' | 'github' | 'profile';
  setActiveView: (view: 'vscode' | 'leetcode' | 'github' | 'profile') => void;

  // LeetCode DSA Engine State
  problems: ProblemItem[];
  setProblems: (problems: ProblemItem[]) => void;
  activeProblem: ProblemItem | null;
  setActiveProblem: (problem: ProblemItem | null) => void;
  selectedLanguage: string;
  setSelectedLanguage: (lang: string) => void;

  // Execution State
  isExecuting: boolean;
  setIsExecuting: (executing: boolean) => void;
  executionResult: ExecutionResult | null;
  setExecutionResult: (res: ExecutionResult | null) => void;
  terminalOutput: string;
  appendTerminalOutput: (msg: string) => void;
  clearTerminalOutput: () => void;

  // VSCode Workspace File Tree State
  files: WorkspaceFile[];
  activeFileId: string | null;
  openFileIds: string[];
  setFiles: (files: WorkspaceFile[]) => void;
  setActiveFile: (id: string) => void;
  openFileTab: (id: string) => void;
  closeFileTab: (id: string) => void;
  updateFileContent: (id: string, content: string) => void;
  createFile: (name: string, path: string, content?: string) => void;
  deleteFile: (id: string) => void;

  // AI Copilot State
  isAiOpen: boolean;
  toggleAiDrawer: () => void;
  aiMessages: AIMessage[];
  addAiMessage: (msg: Omit<AIMessage, 'id' | 'timestamp'>) => void;
  clearAiMessages: () => void;

  // Code Editor Text
  editorCode: string;
  setEditorCode: (code: string) => void;
}

const DEFAULT_FILES: WorkspaceFile[] = [
  {
    id: 'f-1',
    path: 'main.py',
    name: 'main.py',
    content: `import time

def two_sum_hashmap(nums: list[int], target: int) -> list[int]:
    """Optimized O(N) Hash Table complement lookup."""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

if __name__ == "__main__":
    print("🚀 CodeForge AI Execution Engine")
    nums = [2, 7, 11, 15]
    target = 9
    start = time.perf_counter()
    result = two_sum_hashmap(nums, target)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"Input: nums={nums}, target={target}")
    print(f"Indices Result: {result}")
    print(f"Executed in {elapsed:.3f} ms")
`,
    is_directory: false,
    language: 'python',
  },
  {
    id: 'f-2',
    path: 'utils/lru_cache.py',
    name: 'lru_cache.py',
    content: `class Node:
    def __init__(self, key: int, val: int):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key: int) -> int:
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add(node)
            return node.val
        return -1
`,
    is_directory: false,
    language: 'python',
  },
];

const DEFAULT_PROBLEMS: ProblemItem[] = [
  {
    id: 'p-1',
    slug: 'two-sum',
    title: '1. Two Sum',
    difficulty: 'Easy',
    category: 'Arrays',
    acceptance_rate: 52.4,
    description_md: `Given an array of integers \`nums\` and an integer \`target\`, return *indices of the two numbers such that they add up to \`target\`*.

You may assume that each input would have ***exactly one solution***, and you may not use the same element twice.

### Example 1:
\`\`\`text
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
\`\`\`

### Example 2:
\`\`\`text
Input: nums = [3,2,4], target = 6
Output: [1,2]
\`\`\`
`,
    starter_code: {
      python: `def twoSum(nums: list[int], target: int) -> list[int]:
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []
`,
      javascript: `function twoSum(nums, target) {
    const seen = new Map();
    for (let i = 0; i < nums.length; i++) {
        const diff = target - nums[i];
        if (seen.has(diff)) {
            return [seen.get(diff), i];
        }
        seen.set(nums[i], i);
    }
    return [];
}
`,
    },
    test_cases: [
      { input: { nums: [2, 7, 11, 15], target: 9 }, expected_output: '[0, 1]', is_sample: true },
      { input: { nums: [3, 2, 4], target: 6 }, expected_output: '[1, 2]', is_sample: true },
      { input: { nums: [3, 3], target: 6 }, expected_output: '[0, 1]', is_sample: false },
    ],
    constraints: ['2 <= nums.length <= 10^4', '-10^9 <= nums[i] <= 10^9', 'Only one valid answer exists.'],
  },
  {
    id: 'p-2',
    slug: 'valid-anagram',
    title: '242. Valid Anagram',
    difficulty: 'Easy',
    category: 'Strings',
    acceptance_rate: 64.1,
    description_md: `Given two strings \`s\` and \`t\`, return \`true\` *if \`t\` is an anagram of \`s\`, and \`false\` otherwise*.

### Example 1:
\`\`\`text
Input: s = "anagram", t = "nagaram"
Output: true
\`\`\`
`,
    starter_code: {
      python: `def isAnagram(s: str, t: str) -> bool:
    if len(s) != len(t):
        return False
    count = {}
    for char in s:
        count[char] = count.get(char, 0) + 1
    for char in t:
        if char not in count or count[char] == 0:
            return False
        count[char] -= 1
    return True
`,
    },
    test_cases: [
      { input: { s: 'anagram', t: 'nagaram' }, expected_output: 'True', is_sample: true },
      { input: { s: 'rat', t: 'car' }, expected_output: 'False', is_sample: true },
    ],
    constraints: ['1 <= s.length, t.length <= 5 * 10^4'],
  },
  {
    id: 'p-3',
    slug: 'lru-cache',
    title: '146. LRU Cache',
    difficulty: 'Medium',
    category: 'Design',
    acceptance_rate: 42.8,
    description_md: `Design a data structure that follows the constraints of a **Least Recently Used (LRU) Cache**.

Functions \`get\` and \`put\` must each run in \\(O(1)\\) average time complexity.
`,
    starter_code: {
      python: `class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}

    def get(self, key: int) -> int:
        return self.cache.get(key, -1)

    def put(self, key: int, value: int) -> None:
        self.cache[key] = value
`,
    },
    test_cases: [
      { input: { capacity: 2 }, expected_output: 'OK', is_sample: true },
    ],
    constraints: ['1 <= capacity <= 3000'],
  },
];

export const useAppStore = create<AppState>((set, get) => ({
  activeView: 'vscode',
  setActiveView: (view) => set({ activeView: view }),

  problems: DEFAULT_PROBLEMS,
  setProblems: (problems) => set({ problems }),
  activeProblem: DEFAULT_PROBLEMS[0],
  setActiveProblem: (problem) => {
    if (!problem) return;
    const lang = get().selectedLanguage;
    const starter = problem.starter_code?.[lang] || problem.starter_code?.python || '';
    set({ activeProblem: problem, editorCode: starter });
  },

  selectedLanguage: 'python',
  setSelectedLanguage: (lang) => {
    const prob = get().activeProblem;
    const starter = prob?.starter_code?.[lang] || get().editorCode;
    set({ selectedLanguage: lang, editorCode: starter });
  },

  isExecuting: false,
  setIsExecuting: (isExecuting) => set({ isExecuting }),
  executionResult: null,
  setExecutionResult: (executionResult) => set({ executionResult }),

  terminalOutput: 'CodeForge AI v0.1.0 Ready. Press Ctrl+Enter to execute.\n',
  appendTerminalOutput: (msg) => set((s) => ({ terminalOutput: s.terminalOutput + msg + '\n' })),
  clearTerminalOutput: () => set({ terminalOutput: '' }),

  files: DEFAULT_FILES,
  activeFileId: 'f-1',
  openFileIds: ['f-1', 'f-2'],
  setFiles: (files) => set({ files }),
  setActiveFile: (id) => {
    const file = get().files.find((f) => f.id === id);
    if (file) {
      set({ activeFileId: id, editorCode: file.content, selectedLanguage: file.language });
    }
  },
  openFileTab: (id) => {
    const ids = get().openFileIds;
    if (!ids.includes(id)) {
      set({ openFileIds: [...ids, id] });
    }
    get().setActiveFile(id);
  },
  closeFileTab: (id) => {
    const ids = get().openFileIds.filter((i) => i !== id);
    const newActive = ids.length > 0 ? ids[ids.length - 1] : null;
    set({ openFileIds: ids });
    if (newActive) get().setActiveFile(newActive);
  },
  updateFileContent: (id, content) => {
    set((s) => ({
      files: s.files.map((f) => (f.id === id ? { ...f, content } : f)),
      editorCode: s.activeFileId === id ? content : s.editorCode,
    }));
  },
  createFile: (name, path, content = '') => {
    const newFile: WorkspaceFile = {
      id: `f-${Date.now()}`,
      name,
      path: path || name,
      content,
      is_directory: false,
      language: name.endsWith('.js') ? 'javascript' : 'python',
    };
    set((s) => ({
      files: [...s.files, newFile],
      openFileIds: [...s.openFileIds, newFile.id],
      activeFileId: newFile.id,
      editorCode: content,
    }));
  },
  deleteFile: (id) => {
    get().closeFileTab(id);
    set((s) => ({ files: s.files.filter((f) => f.id !== id) }));
  },

  isAiOpen: true,
  toggleAiDrawer: () => set((s) => ({ isAiOpen: !s.isAiOpen })),
  aiMessages: [
    {
      id: 'm-1',
      sender: 'assistant',
      content:
        '👋 Welcome to CodeForge AI! I am your FAANG-level AI Copilot. Ask me to explain code, debug errors, generate unit tests, or provide DSA hints.',
      timestamp: '10:00 AM',
    },
  ],
  addAiMessage: (msg) =>
    set((s) => ({
      aiMessages: [
        ...s.aiMessages,
        {
          id: `m-${Date.now()}`,
          ...msg,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ],
    })),
  clearAiMessages: () => set({ aiMessages: [] }),

  editorCode: DEFAULT_FILES[0].content,
  setEditorCode: (editorCode) => set({ editorCode }),
}));
