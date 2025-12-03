# Verification Report: vibetools

Generated: 2025-12-03T18:55:35.785109Z

Total chunks: 36352


## Query 1: How do agents handle errors and exceptions?

- Result 1: `expert-cpp-software-engineer.chatmode.md` — distance: 0.812714
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/expert-cpp-software-engineer.chatmode.md
  - preview: '''
- **Error Handling and Contracts**: Apply a consistent policy (exceptions or suitable alternatives) with clear contracts and safety guarantees appropriate to the codebase.
'''

- Result 2: `blazor.instructions.md` — distance: 0.840219
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/blazor.instructions.md
  - preview: '''
- Implement error handling for API calls using try-catch and provide proper user feedback in the UI.
'''

- Result 3: `dotnet-maui.instructions.md` — distance: 0.840219
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/dotnet-maui.instructions.md
  - preview: '''
- Implement error handling for API calls using try-catch and provide proper user feedback in the UI.
'''

- Result 4: `dart-n-flutter.instructions.md` — distance: 0.85386765
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/dart-n-flutter.instructions.md
  - preview: '''
*   DO throw objects that implement `Error` only for programmatic errors.
*   DON'T explicitly catch `Error` or types that implement it.
*   DO use `rethrow` to rethrow a caught exception.
'''

- Result 5: `power-bi-dax-best-practices.instructions.md` — distance: 0.85767245
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/power-bi-dax-best-practices.instructions.md
  - preview: '''
### 3. Error Handling Strategies
Implement robust error handling using appropriate patterns:
'''


## Query 2: What are the main classes and functions?

- Result 1: `create-oo-component-documentation.prompt.md` — distance: 0.9063998
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/prompts/create-oo-component-documentation.prompt.md
  - preview: '''
- **Component structure** - Main classes, interfaces, and their relationships
- **Internal dependencies** - How components interact within the system
'''

- Result 2: `update-oo-component-documentation.prompt.md` — distance: 0.9819431
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/prompts/update-oo-component-documentation.prompt.md
  - preview: '''
- **Component structure** - Current classes, interfaces, and their relationships
- **Internal dependencies** - How components currently interact within the system
'''

- Result 3: `ruby-on-rails.instructions.md` — distance: 1.007869
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/ruby-on-rails.instructions.md
  - preview: '''
- Apply the Single Responsibility Principle to classes, methods, and modules.
- Prefer composition over inheritance; extract reusable logic into modules or services.
'''

- Result 4: `power-apps-canvas-yaml.instructions.md` — distance: 1.0343281
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/power-apps-canvas-yaml.instructions.md
  - preview: '''
- **Functional**: Avoids side effects; most functions are pure
- **Composition**: Complex logic built by combining simpler functions
- **Strongly Typed**: Type system ensures data integrity
'''

- Result 5: `mentor.chatmode.md` — distance: 1.0450928
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/mentor.chatmode.md
  - preview: '''
You can look through the codebase, search for relevant files, and find usages of functions or classes to understand the context of the problem and help the engineer understand how things work.
'''


## Query 3: How is configuration managed?

- Result 1: `folder-structure-blueprint-generator.prompt.md` — distance: 0.5926407
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/prompts/folder-structure-blueprint-generator.prompt.md
  - preview: '''
- **Configuration Management**:
  - Configuration file locations and purposes
  - Environment-specific configurations
  - Secret management approach
'''

- Result 2: `devops-core-principles.instructions.md` — distance: 0.5978067
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/devops-core-principles.instructions.md
  - preview: '''
- **Configuration Management:** Automate the configuration of servers and application environments (e.g., Ansible, Puppet, Chef).
'''

- Result 3: `architecture-blueprint-generator.prompt.md` — distance: 0.6546175
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/prompts/architecture-blueprint-generator.prompt.md
  - preview: '''
- **Configuration Management**:
  - Configuration source patterns
  - Environment-specific configuration strategies
  - Secret management approach
  - Feature flag implementation
'''

- Result 4: `nestjs.instructions.md` — distance: 0.71021056
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/nestjs.instructions.md
  - preview: '''
## Configuration Management
'''

- Result 5: `power-bi-devops-alm-best-practices.instructions.md` — distance: 0.71021056
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/power-bi-devops-alm-best-practices.instructions.md
  - preview: '''
## Configuration Management
'''


## Query 4: How to set up CI/CD for agent pipelines?

- Result 1: `github-actions-ci-cd-best-practices.instructions.md` — distance: 0.5900438
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/github-actions-ci-cd-best-practices.instructions.md
  - preview: '''
guide developers in building highly efficient, secure, and reliable CI/CD pipelines. Remember that CI/CD is an iterative journey; continuously measure, optimize, and secure your pipelines to achieve
'''

- Result 2: `devops-architect.prompt.md` — distance: 0.5907566
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/agents/devops-architect.prompt.md
  - preview: '''
### 2. Design CI/CD Pipelines
'''

- Result 3: `devops-core-principles.instructions.md` — distance: 0.5925389
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/devops-core-principles.instructions.md
  - preview: '''
- When generating CI/CD pipelines, design them for frequent, small, and safe deployments. Suggest automation to reduce deployment friction (e.g., automated testing, blue/green deployments).
'''

- Result 4: `github-actions-ci-cd-best-practices.instructions.md` — distance: 0.60173225
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/github-actions-ci-cd-best-practices.instructions.md
  - preview: '''
testing and robust deployment strategies—you can guide developers in building highly efficient, secure, and reliable CI/CD pipelines. Remember that CI/CD is an iterative journey; continuously
'''

- Result 5: `github-actions-ci-cd-best-practices.instructions.md` — distance: 0.6115509
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/github-actions-ci-cd-best-practices.instructions.md
  - preview: '''
implementing comprehensive testing and robust deployment strategies—you can guide developers in building highly efficient, secure, and reliable CI/CD pipelines. Remember that CI/CD is an iterative
'''


## Query 5: How to write Playwright E2E tests?

- Result 1: `playwright-typescript.instructions.md` — distance: 0.49923122
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/instructions/playwright-typescript.instructions.md
  - preview: '''
---
description: 'Playwright test generation instructions'
applyTo: '**'
---

## Test Writing Guidelines
'''

- Result 2: `playwright-typescript.instructions.md` — distance: 0.49923122
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/prompts/playwright-typescript.instructions.md
  - preview: '''
---
description: 'Playwright test generation instructions'
applyTo: '**'
---

## Test Writing Guidelines
'''

- Result 3: `playwright-tester.chatmode.md` — distance: 0.59694374
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/playwright-tester.chatmode.md
  - preview: '''
---
description: 'Testing mode for Playwright tests'
'''

- Result 4: `playwright-generate-test.prompt.md` — distance: 0.6873945
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/prompts/playwright-generate-test.prompt.md
  - preview: '''
- You are given a scenario, and you need to generate a playwright test for it. If the user does not provide a scenario, you will ask them to provide one.
'''

- Result 5: `playwright-tester.chatmode.md` — distance: 0.74210596
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/playwright-tester.chatmode.md
  - preview: '''
3.  **Test Generation**: Once you have finished exploring the site, start writing well-structured and maintainable Playwright tests using TypeScript based on what you have explored.
'''


## Query 6: How to ingest code and debug ingestion errors?

- Result 1: `4.1-Beast.chatmode.md` — distance: 0.7072904
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/4.1-Beast.chatmode.md
  - preview: '''
- Read and understand relevant code snippets.
- Identify the root cause of the problem.
- Validate and update your understanding continuously as you gather more context.
'''

- Result 2: `Thinking-Beast-Mode.chatmode.md` — distance: 0.7072904
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/Thinking-Beast-Mode.chatmode.md
  - preview: '''
- Read and understand relevant code snippets.
- Identify the root cause of the problem.
- Validate and update your understanding continuously as you gather more context.
'''

- Result 3: `rust-gpt-4.1-beast-mode.chatmode.md` — distance: 0.7072904
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/rust-gpt-4.1-beast-mode.chatmode.md
  - preview: '''
- Read and understand relevant code snippets.
- Identify the root cause of the problem.
- Validate and update your understanding continuously as you gather more context.
'''

- Result 4: `4.1-Beast.chatmode.md` — distance: 0.752719
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/4.1-Beast.chatmode.md
  - preview: '''
- Make code changes only if you have high confidence they can solve the problem
- When debugging, try to determine the root cause rather than addressing symptoms
'''

- Result 5: `Thinking-Beast-Mode.chatmode.md` — distance: 0.752719
  - source: /home/ob/Development/Tools/vibe-tools/ghc_tools/chatmodes/Thinking-Beast-Mode.chatmode.md
  - preview: '''
- Make code changes only if you have high confidence they can solve the problem
- When debugging, try to determine the root cause rather than addressing symptoms
'''
