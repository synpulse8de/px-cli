# PulseX Command Line Interface (CLI)

*Looking for [installation instructions](installation.md)?*

## 🚗 Basic usage

```bash
# first time - authenticate
pulseX auth login firstname.lastname@synpulse.com

# run the CLI
pulseX
```

## Create a new project from template

1. Start by running one of the below commands, depending on your project need:

    ```bash
    pulseX backend create               # Java Spring Boot (Our standard)
    pulseX backend-fastapi create       # Python FastAPI
    pulseX backend-shared-lib create    # Java libraries
    pulseX frontend create              # NextJS-based frontends
    pulseX frontend-angular create      # Angular-based frontends
    ```

1. Follow the prompts provided to create your project 😎 See example below for a basic backend project:

    ```bash
    $ pulseX backend create
    running template precheck...
    GitHub authentication set to user antti-viitala_SYNPULSE
    template precheck done - continue...
    Do you want to create private remote repository ? [y/N]: N
    Pulling latest template data...
    🎤 1. Project Name (PulseX <Archetype> <Name>)
        PulseX Example Project Backend
    🎤 2. Project Id (pulseX-<archetype>-<name>) - folder name, used in different settings (docker or k8s image names, ...)
        pulseX-example-project-backend
    🎤 3. Short project Description (leave empty to skip)
        Something interesting would come here
    🎤 4. Maven groupId
        com.synpulse8.pulseX.core
    🎤 5. Maven artifactId
        example-project-backend
    ...

    Copying from template version 0.0.5
    identical  .
        create  .husky
        create  .husky/pre-push
        create  .husky/pre-commit
        create  pom.xml
    ...

    Initialized empty Git repository in /Users/aviitala/dev-work/core/pulseX-core-cli/pulseX-example-project-backend/.git/
    Committed generated project. Happy coding!
    ```

1. Get to coding!
