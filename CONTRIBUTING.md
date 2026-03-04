# Contributing to VisiSense

Thank you for your interest in contributing to the **VisiSense - Visual Product Intelligence Blueprint** by Cloud2 Labs.

## Scope of Contributions

Appropriate contributions include:
- Documentation improvements
- Bug fixes and issue reports
- Reference architecture enhancements
- Code quality improvements
- Multi-provider support enhancements
- Test coverage improvements
- Performance optimizations
- Security best practice implementations

## How to Contribute

1. **Fork the Repository**
   - Create a fork of the VisiSense repository

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow existing code style and patterns
   - Add tests if applicable
   - Update documentation as needed

4. **Test Your Changes**
   - Ensure all existing tests pass
   - Test with multiple LLM providers if applicable
   - Verify Docker builds work correctly

5. **Submit a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

## Code Style Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions focused and concise
- Remove unnecessary comments
- Avoid hardcoding provider-specific logic

## Provider-Agnostic Principles

- Use generic terminology (avoid "OpenAI", "Groq", etc. in logs)
- Support configuration via environment variables
- Test with multiple providers when possible
- Document provider-specific requirements

## Questions?

Open an issue for discussion or contact Cloud2 Labs for guidance.
