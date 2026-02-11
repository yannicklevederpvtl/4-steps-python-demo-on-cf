# Cloud Foundry FAQ & Resources

FAQ and documentation links for the platform components used in this workshop.

## FAQ

### Beginner questions

- **Where do I find the `cf push` docs? What is `cf push`?**  
  [Pushing your app with Cloud Foundry CLI (cf push)](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/deploy-apps-deploy-app.html) — explains what `cf push` does, prerequisites, and how to deploy.

- **How do I deploy using a manifest file?**  
  [Deploying with app manifests](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/deploy-apps-manifest.html) — `manifest.yml` (or `-f`), attributes, and how they interact with the CLI.


### How do I use a different Postgres or embedding service name?
Edit the `manifest-uv.yml` (or `manifest-pip.yml`) in the project: update the `services` list and, if your app reads them, the env vars `VECTOR_DB_SERVICE_NAME` and `EMBEDDING_SERVICE_NAME`. See the root [README](README.md#service-configuration) for details.

### Where do service credentials come from?
Bound services inject credentials via the `VCAP_SERVICES` environment variable. See also [Tanzu Platform concepts](#tanzu-platform-concepts) below (VCAP_SERVICES, service binding). For GenAI/embedding services, see the *Binding credentials format* link under [Tanzu AI Services](#tanzu-ai-services) below.

---

## Tanzu Platform concepts

Short explanations and links to where each concept is described in the docs:

- **What is `cf push`?** — Deploys your app to Tanzu Application Service (staging + starting). [Pushing your app with Cloud Foundry CLI (cf push)](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/deploy-apps-deploy-app.html)

- **What is a route?** — A hostname/path/port that sends traffic to your app. The router (Gorouter) maps routes to app instances. [HTTP routing](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/http-routing.html) · [cf create-route](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/cf-cli-cmds-create-route.html)

- **What is `VCAP_SERVICES`?** — A JSON environment variable injected into your app with credentials for every bound service (host, port, username, password, etc.). [Environment variables](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/deploy-apps-environment-variable.html) · [Binding credentials](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/tanzu-platform-for-cloud-foundry/10-3/tpcf/binding-credentials.html)

- **What is service binding?** — Linking a service instance (e.g. Postgres) to an app so the app gets credentials via `VCAP_SERVICES`. [Binding a service instance to an application](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/tanzu-platform-for-cloud-foundry/10-3/tpcf/services-application-binding.html)

- **What is a buildpack?** — Scripts that detect your app type and build a runnable "droplet" (e.g. install runtime, dependencies). [How applications are staged](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/how-applications-are-staged.html)

- **What is an app manifest?** — A YAML file (e.g. `manifest.yml`) that defines app name, memory, routes, services, and other options so you don't pass everything on the `cf push` command line. [Deploying with app manifests](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/deploy-apps-manifest.html)

- **What is the marketplace?** — The set of services (e.g. Postgres, AI embedding) you can create and bind to apps. You use `cf marketplace`, `cf create-service`, and `cf bind-service`. [Adding services from the marketplace](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/tanzu-platform-for-cloud-foundry/10-3/tpcf/adding-services-marketplace.html) (Apps Manager); CLI flow is in the deploy and binding docs above.

- **What is a 12-factor app?** — A methodology for building software-as-a-service apps that use declarative setup, stay portable, treat backing services as attached resources, and scale on cloud platforms with minimal divergence between dev and production. TAS and Cloud Foundry are designed to run 12-factor-style apps. [The Twelve-Factor App](https://12factor.net/)

  **The twelve factors (high level):** (I) One codebase, many deploys · (II) Explicit, isolated dependencies · (III) Config in the environment · (IV) Backing services as attached resources · (V) Strict build, release, run separation · (VI) Stateless processes · (VII) Port binding to export the app · (VIII) Concurrency via the process model · (IX) Fast startup, graceful shutdown · (X) Dev/prod parity · (XI) Logs as event streams · (XII) Admin tasks as one-off processes.

  **Videos:** [Twelve-Factor App overview](https://www.youtube.com/watch?v=QOz1UOf6MdU) · [Twelve-Factor App (video)](https://www.youtube.com/watch?v=3ziP2wIbNXo)

---

## Resources

### Tanzu Postgres (Postgres tile)
- [Tanzu for Postgres on Tanzu Platform](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/tanzu-postgres-tanzu-platform/1-2/postgres-tp/install.html) — tile install and configuration

### Tanzu AI Services
- [AI Services](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-3/ai/index.html) — overview, embedding models, and integrations
- [Binding credentials format (GenAI on TAS for Cloud Foundry)](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform-services/genai-on-tanzu-platform-for-cloud-foundry/10-3/ai-cf/reference-binding-credentials-format.html) — `VCAP_SERVICES` and model capabilities (e.g. embedding)

### Elastic Application Runtime (TAS)
- [Elastic Application Runtime — concepts overview](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/concepts-overview.html) — runtime architecture and components
