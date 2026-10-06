# Contributed project icon sources

Original assets are stored without changes. Contribution cards embed the originals at consistent display sizes and use the official light and dark LiteLLM variants.

| Project | Local file | Official source |
| --- | --- | --- |
| SWE-bench | `swe-bench.png` | [SWE-bench GitHub organization](https://github.com/SWE-bench) · [Organization avatar](https://avatars.githubusercontent.com/u/139597579?v=4&s=96) |
| Paseo | `paseo.svg` | [Official app icon](https://github.com/getpaseo/paseo/blob/main/packages/app/assets/images/favicon-light.svg) |
| pydantic-ai | `pydantic-ai.png` | [Pydantic GitHub organization](https://github.com/pydantic) · [Organization avatar](https://avatars.githubusercontent.com/u/110818415?v=4&s=96) |
| LiteLLM | `litellm-light.svg`, `litellm-dark.svg` | [Light monogram](https://github.com/BerriAI/litellm/blob/main/ui/litellm-dashboard/public/assets/logos/litellm_monogram.svg) · [Dark monogram](https://github.com/BerriAI/litellm/blob/main/ui/litellm-dashboard/public/assets/logos/litellm_monogram_dark.svg) |
| Hindsight | `hindsight.png` | [Documentation icon](https://github.com/vectorize-io/hindsight/blob/main/hindsight-docs/static/img/favicon.png) |
| Pi | `pi-logo.svg` | [Logo linked by the project README](https://pi.dev/logo-auto.svg) |

The cards use Tabler's unchanged [star icon](https://github.com/tabler/tabler-icons/blob/main/icons/outline/star.svg), with its stroke color inherited from the card. Its MIT license is included in `../tech/LICENSE.tabler-icons`.

`.github/scripts/render_contributions.py` reads `projects.json`, fetches each repository's current `stargazers_count` through the GitHub API, and generates light and dark SVG cards. Each count refers to the exact repository linked alongside it, including `SWE-bench/experiments`.

The profile graphics workflow publishes the cards to `output/contributions/` daily at 09:17 China time, together with the contribution snake. GitHub's image cache can delay display updates.

These assets identify projects the profile owner has contributed to. Brand rights remain with their respective owners.
