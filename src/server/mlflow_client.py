"""MLflow Prompt Registry integration layer.

Uses the dedicated MLflow Prompt APIs (search_prompts, search_prompt_versions,
load_prompt) rather than the generic registered model APIs.

Unity Catalog prompts require catalog + schema for search, so the list_prompts
endpoint accepts those as parameters.
"""

import logging
import warnings
import mlflow
from server.mlflow_helpers import configure_mlflow, get_mlflow_client
from server.templates import parse_template_variables

logger = logging.getLogger(__name__)


def _paginate(client, method_name: str, kwargs: dict, token_attr: str = "token"):
    """Generic paginator for MLflow search APIs.

    Yields result pages. The caller iterates over items in each page.
    Different MLflow APIs use different token attribute names (token vs next_page_token).
    """
    page_token = None
    while True:
        if page_token:
            kwargs["page_token"] = page_token
        result = getattr(client, method_name)(**kwargs)
        yield result
        tok = getattr(result, token_attr, None)
        if not tok:
            break
        page_token = tok


def list_prompts(catalog: str = "main", schema: str = "default") -> list[dict]:
    """List all registered prompts in a given UC catalog.schema.

    Unity Catalog prompt registries require catalog and schema to be specified.
    """
    client = get_mlflow_client()
    filter_string = f"catalog = '{catalog}' AND schema = '{schema}'"
    prompts = []

    try:
        for result in _paginate(client, "search_prompts", {"filter_string": filter_string, "max_results": 100}):
            for p in result:
                tags = {}
                if hasattr(p, "tags") and p.tags and not callable(p.tags):
                    tags = dict(p.tags) if isinstance(p.tags, dict) else {}

                prompts.append({
                    "name": p.name,
                    "description": getattr(p, "description", "") or "",
                    "tags": tags,
                })
    except Exception as e:
        logger.error("Error listing prompts for %s.%s: %s", catalog, schema, e)
        raise

    return prompts


def get_prompt_versions(name: str) -> list[dict]:
    """Get all versions for a prompt.

    The name should be fully qualified: catalog.schema.prompt_name
    """
    client = get_mlflow_client()
    versions_out = []

    try:
        for result in _paginate(client, "search_prompt_versions", {"name": name, "max_results": 100}, token_attr="next_page_token"):
            items = result.prompt_versions if hasattr(result, "prompt_versions") else result

            for v in items:
                ts = None
                if hasattr(v, "creation_timestamp"):
                    ct = v.creation_timestamp
                    if hasattr(ct, "seconds"):
                        ts = ct.seconds * 1000
                    elif isinstance(ct, (int, float)):
                        ts = int(ct)

                aliases = []
                if hasattr(v, "aliases"):
                    aliases = list(v.aliases)

                versions_out.append({
                    "version": str(v.version),
                    "description": getattr(v, "description", "") or "",
                    "aliases": aliases,
                    "template_preview": (v.template[:120] + "...") if hasattr(v, "template") and v.template and len(v.template) > 120 else (v.template if hasattr(v, "template") else ""),
                    "creation_timestamp": ts,
                })
    except Exception as e:
        logger.error("Error getting versions for %s: %s", name, e)
        raise

    # Sort newest first
    versions_out.sort(key=lambda x: int(x["version"]), reverse=True)
    return versions_out


def get_prompt_template(name: str, version: str) -> dict:
    """Load a prompt template by name and version/alias.

    The name should be fully qualified: catalog.schema.prompt_name
    """
    configure_mlflow()  # needed for mlflow.genai.load_prompt (no client involved)

    uri = f"prompts:/{name}/{version}"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            prompt = mlflow.genai.load_prompt(uri)

        template = prompt.template

        # Always parse from template to preserve the order variables appear in the text
        variables = parse_template_variables(template)

        tags = {}
        if hasattr(prompt, "tags") and prompt.tags:
            if isinstance(prompt.tags, dict):
                tags = prompt.tags
            else:
                try:
                    tags = dict(prompt.tags)
                except Exception:
                    pass

        return {
            "name": name,
            "version": str(prompt.version) if hasattr(prompt, "version") else version,
            "template": template,
            "variables": variables,
            "tags": tags,
            "aliases": list(prompt.aliases) if hasattr(prompt, "aliases") and prompt.aliases else [],
        }
    except Exception as e:
        logger.error("Error loading prompt %s: %s", uri, e)
        raise ValueError(f"Could not load prompt '{name}' version '{version}': {e}")


def create_prompt(name: str, template: str, description: str = "") -> dict:
    """Create a brand new prompt in the Unity Catalog Prompt Registry.

    The name should be fully qualified: catalog.schema.prompt_name
    Creates the prompt entity first, then its initial version with the template.
    Returns dict with {name, version, template, variables}.
    """
    client = get_mlflow_client()

    # create_prompt creates the entity (no template); then create the first version
    client.create_prompt(name=name, description=description)
    prompt_version = client.create_prompt_version(
        name=name,
        template=template,
        description=description,
    )

    return {
        "name": name,
        "version": str(prompt_version.version),
        "template": template,
        "variables": parse_template_variables(template),
    }


def create_prompt_version(name: str, template: str, description: str = "") -> dict:
    """Create a new version of an existing prompt.

    The name should be fully qualified: catalog.schema.prompt_name
    Returns dict with {name, version, template, variables}.
    """
    client = get_mlflow_client()

    prompt_version = client.create_prompt_version(
        name=name,
        template=template,
        description=description,
    )

    return {
        "name": name,
        "version": str(prompt_version.version),
        "template": template,
        "variables": parse_template_variables(template),
    }
