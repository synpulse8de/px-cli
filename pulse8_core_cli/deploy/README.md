# Pulse8 CLI: `deploy` module

## High-level commands

- `create` - collect all information
- `update` - similar to create but edit existing info
- `submit` - submit a deployment configuration for deployment (e.g. sync repo, branch out, open PR)

### `create` / `update`

1. Authenticate/set up CLI
1. **TBC: Whether this is (a) something that runs in the background or a separate command**
    - Clone `pulse8-app-deployments` into some temp folder managed by the CLI for later use
    - This info is a must so that we can have the right configuration options available for `create`
1. Navigate to the root of the project/directory they wish to deploy, e.g. `my-project` as shown below

    ```bash
    $ cd my-project/
    $ ls
    my-project/
    ├── k8s/
    ├── my-code/
    └── README.md
    ```

1. Run `deploy create`
    - Validate/pre-work:
        - Ensure that a local clone of `pulse8-app-deployments` exists
        - checkout to `main`, and `git pull` to ensure it is up to date
    - Prompts:
        - ~~Select: Target cluster (based on which clusters are available in `/clusters/` folder of deployments repo)~~ (removed from MVP, anyway we just have the one cluster atm)
        - Text input: Project name (automate this, based on repo name perhaps?)
        - Text input: Port selection
        - Select: Want database? (if yes --> create configmap entry + external secret, figure out how to update `databases.tf` so it gets generated)
        - Select: Hardware resource selection
            - `small`: 0.1m CPU / 256 Mi (default)
            - `medium`: 0.25m CPU / 512 Mi
            - `large`: 0.75m CPU / 1024 Mi
        - Text input: Provide subdomain URL (i.e. `$ENV.$APP_NAME$.pulse8.aws.synpulse8.com`, or have this depend on the cluster info? Perhaps add `cluster-info.yaml` to the deployments repo's clusters folder)
        - Select: Environments (dev/uat/prod), then for each the below:
            - Text input or automatic input: Deployment image
            - Text input or auto: Image selection method/regex (can I immediately verify that this exists?)
                - Image pattern: Can I verify it immediately?
        - **Deal with configmaps/secrets**
    - Process:
        - Save selections in some local file, following pulse8 cli standard
1. Generate the required manifests under the current project, following a structure like this:

    ```bash
    my-project/
    ├── k8s/
    │   ├── $NAME_OF_CLUSTER/ # 'real' deployment we're building/
    │   │   └── k8s/ # add a gitignore here, nothing should be checked in.
    │   │       ├── base/ # base is always included
    │   │       ├── dev/  # if selected
    │   │       ├── uat/  # if selected
    │   │       ├── prod/  # if selected
    │   │       └── flux-deployments/ # deployment manifests - always included
    │   └── base/ # manifests used by pulse8 CLI for local stuff
    ├── my-code/
    └── README.md
    ```

### `submit`

1. Check that project has the proper deployment manifests (i.e. ensure `create` has been ran at least once)
1. Update the `pulse8-app-deployments` repo managed by the CLI
1. Checkout to new branch `feat/add-deployment/$REPO_NAME` (If a branch exists, perhaps delete it first? we need to be fresh)
1. Copy contents:
    - from: `./k8s/$NAME_OF_CLUSTER/k8s/`
    - to:
        - defs: `pulse8-app-deployments/application-definitions/$PROJECT_NAME`
            - This will bring in the `kustomize` layers for all envs
            - Remember to create a README
        - deploys: `clusters/$RELEVANT_CLUSTER/$PROJECT_NAME/`, one file for each env, `$PROJECT_NAME_$ENV.yaml`
1. Commit
1. Push
1. Create PR against main (perhaps with `gh` CLI)
1. Once done, checkout back to main on the local CLI-managed repo

## Notes

- Shared component: Check/verify that we are in a pulse8 project directory? all commands have to do this at the start
- Try to implement each input selection as a closed function, that loops forever until a valid input is given or user decides to Ctrl+C out (in which case, set a sensible default if possible)
