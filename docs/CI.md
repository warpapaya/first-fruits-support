# Support site checks

Run `python3 -m unittest discover -s tests -v`. Tests use Python's standard library and serve the actual pages from localhost. They check support/privacy page responses, relative links and fragments, reciprocal navigation, contact email, mobile viewport, document structure, emergency access and deletion guidance. External links are validated as HTTPS/mailto but never fetched.

Actions runs these checks on pull requests and main pushes. No site deployment or publishing workflow is added. GitHub Pages/manual publication and direct pushes remain outside these checks; requiring the `Served pages and navigation` check needs owner approval. Visual/browser layout and external URL availability remain additional checks.
