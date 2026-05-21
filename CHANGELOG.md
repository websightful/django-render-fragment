# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
...

## [v1.2.0] - 2026-05-21

### Added

- Optional multiline support for better template readability.

## [v1.1.0] - 2026-05-15

### Changed

- Package renamed from `django-template-fragments` to `django-render-fragment` because the former name is already taken.

## [v1.0.0] - 2026-05-15

### Added

- Initial release of `django-template-fragments` with template tag `render_fragment` that autonomously renders a template fragment and optionally saves it into a context variable.  
- Includes tests covering all template tag parameter variations.  
- `tox` setup to test against multiple Django versions.

<!--
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
-->
