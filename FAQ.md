# Cloud Foundry FAQ & Resources

FAQ and documentation links for the platform components used in this workshop.

## FAQ

### How do I use a different Postgres or embedding service name?
Edit the `manifest-uv.yml` (or `manifest-pip.yml`) in the project: update the `services` list and, if your app reads them, the env vars `VECTOR_DB_SERVICE_NAME` and `EMBEDDING_SERVICE_NAME`. See the root [README](README.md#service-configuration) for details.

### Where do service credentials come from?
Bound services inject credentials via the `VCAP_SERVICES` environment variable. For GenAI/embedding services, see the *Binding credentials format* link under [Tanzu AI Services](#tanzu-ai-services) below.

---

## Resources

### Tanzu Postgres (Postgres tile)
- [Tanzu for Postgres on Tanzu Platform](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/tanzu-postgres-tanzu-platform/1-2/postgres-tp/install.html) — tile install and configuration

### Tanzu AI Services
- [AI Services](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/ai-services/10-3/ai/index.html) — overview, embedding models, and integrations
- [Binding credentials format (GenAI on TAS for Cloud Foundry)](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform-services/genai-on-tanzu-platform-for-cloud-foundry/10-3/ai-cf/reference-binding-credentials-format.html) — `VCAP_SERVICES` and model capabilities (e.g. embedding)

### Elastic Application Runtime (TAS)
- [Elastic Application Runtime — concepts overview](https://techdocs.broadcom.com/us/en/vmware-tanzu/platform/elastic-application-runtime/10-3/eart/concepts-overview.html) — runtime architecture and components
