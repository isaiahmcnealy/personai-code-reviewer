# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Decoupled review core: `PRContext -> review() -> list[Finding]`.
- Reviewer personas: staff engineer, security, performance, readability.
- GitHub adapter (PR URL → `PRContext`) and `personai review` CLI.
- Open-source scaffolding: license, contributing guide, code of conduct,
  architecture doc, CI, issue/PR templates.

Planned work lives in [ROADMAP.md](ROADMAP.md); this changelog records only
what has shipped.

## [0.1.0] - 2026-08-01
- Initial scaffold.
