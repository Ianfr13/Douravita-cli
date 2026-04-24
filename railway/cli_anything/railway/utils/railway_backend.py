"""GraphQL HTTP client for the Railway API.

Endpoint: https://backboard.railway.app/graphql/v2
Auth:     Authorization: Bearer <token>
"""

from __future__ import annotations

import sys
import requests

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"


class RailwayAPIError(Exception):
    """Raised when the Railway API returns errors or an HTTP error status."""

    def __init__(self, message: str, errors: list | None = None):
        super().__init__(message)
        self.errors = errors or []


class RailwayBackend:
    """Thin wrapper around the Railway GraphQL API."""

    def __init__(self, token: str):
        if not token:
            raise RailwayAPIError(
                "No Railway token provided. Set RAILWAY_TOKEN or use --token."
            )
        self._token = token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Low-level request helper
    # ------------------------------------------------------------------

    def query(self, gql: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query or mutation.

        Args:
            gql: GraphQL query/mutation string.
            variables: Optional variables dict.

        Returns:
            The ``data`` field from the GraphQL response.

        Raises:
            RailwayAPIError: On HTTP errors or GraphQL errors.
        """
        payload: dict = {"query": gql}
        if variables:
            payload["variables"] = variables

        try:
            resp = self._session.post(RAILWAY_GRAPHQL_URL, json=payload, timeout=30)
        except requests.RequestException as exc:
            raise RailwayAPIError(f"Network error: {exc}") from exc

        if resp.status_code == 401:
            raise RailwayAPIError(
                "Authentication failed. Check your RAILWAY_TOKEN."
            )

        if not resp.ok:
            raise RailwayAPIError(
                f"HTTP {resp.status_code}: {resp.text[:200]}"
            )

        body = resp.json()
        if "errors" in body and body["errors"]:
            msgs = "; ".join(e.get("message", str(e)) for e in body["errors"])
            raise RailwayAPIError(f"Railway API error: {msgs}", errors=body["errors"])

        return body.get("data", {})

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def projects_list(self) -> list[dict]:
        data = self.query(
            """
            query {
                projects {
                    edges {
                        node {
                            id
                            name
                            description
                            createdAt
                            updatedAt
                        }
                    }
                }
            }
            """
        )
        return [edge["node"] for edge in data.get("projects", {}).get("edges", [])]

    def project_info(self, project_id: str) -> dict:
        data = self.query(
            """
            query GetProject($id: String!) {
                project(id: $id) {
                    id
                    name
                    description
                    createdAt
                    updatedAt
                    environments {
                        edges { node { id name } }
                    }
                    services {
                        edges { node { id name createdAt } }
                    }
                }
            }
            """,
            {"id": project_id},
        )
        return data.get("project", {})

    def project_create(self, name: str) -> dict:
        data = self.query(
            """
            mutation CreateProject($name: String!) {
                projectCreate(input: { name: $name }) {
                    id
                    name
                }
            }
            """,
            {"name": name},
        )
        return data.get("projectCreate", {})

    # ------------------------------------------------------------------
    # Services
    # ------------------------------------------------------------------

    def services_list(self, project_id: str) -> list[dict]:
        data = self.query(
            """
            query GetServices($id: String!) {
                project(id: $id) {
                    services {
                        edges { node { id name createdAt } }
                    }
                }
            }
            """,
            {"id": project_id},
        )
        project = data.get("project", {})
        return [
            edge["node"]
            for edge in project.get("services", {}).get("edges", [])
        ]

    def service_info(self, service_id: str) -> dict:
        data = self.query(
            """
            query GetService($id: String!) {
                service(id: $id) {
                    id
                    name
                    createdAt
                    updatedAt
                }
            }
            """,
            {"id": service_id},
        )
        return data.get("service", {})

    # ------------------------------------------------------------------
    # Deployments
    # ------------------------------------------------------------------

    def deployments_list(
        self, service_id: str, environment_id: str | None = None
    ) -> list[dict]:
        variables: dict = {"serviceId": service_id}
        input_fields = "serviceId: $serviceId"
        var_decl = "$serviceId: String!"
        if environment_id:
            variables["environmentId"] = environment_id
            input_fields += ", environmentId: $environmentId"
            var_decl += ", $environmentId: String!"

        data = self.query(
            f"""
            query GetDeployments({var_decl}) {{
                deployments(input: {{ {input_fields} }}) {{
                    edges {{
                        node {{
                            id
                            status
                            createdAt
                            staticUrl
                        }}
                    }}
                }}
            }}
            """,
            variables,
        )
        return [
            edge["node"]
            for edge in data.get("deployments", {}).get("edges", [])
        ]

    def deployment_trigger(self, service_id: str, environment_id: str) -> bool:
        data = self.query(
            """
            mutation TriggerDeploy($serviceId: String!, $environmentId: String!) {
                serviceInstanceDeploy(
                    serviceId: $serviceId,
                    environmentId: $environmentId
                )
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return bool(data.get("serviceInstanceDeploy"))

    def deployment_status(self, deployment_id: str) -> dict:
        data = self.query(
            """
            query GetDeployment($id: String!) {
                deployment(id: $id) {
                    id
                    status
                    createdAt
                    staticUrl
                }
            }
            """,
            {"id": deployment_id},
        )
        return data.get("deployment", {})

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------

    def variables_list(
        self, project_id: str, environment_id: str, service_id: str | None = None
    ) -> dict:
        vars_query = """
            query GetVariables(
                $projectId: String!,
                $environmentId: String!,
                $serviceId: String
            ) {
                variables(
                    projectId: $projectId,
                    environmentId: $environmentId,
                    serviceId: $serviceId
                )
            }
        """
        v: dict = {"projectId": project_id, "environmentId": environment_id}
        if service_id:
            v["serviceId"] = service_id
        data = self.query(vars_query, v)
        return data.get("variables", {})

    def variable_upsert(
        self,
        project_id: str,
        environment_id: str,
        name: str,
        value: str,
        service_id: str | None = None,
    ) -> bool:
        input_obj: dict = {
            "projectId": project_id,
            "environmentId": environment_id,
            "name": name,
            "value": value,
        }
        if service_id:
            input_obj["serviceId"] = service_id

        data = self.query(
            """
            mutation UpsertVariable($input: VariableUpsertInput!) {
                variableUpsert(input: $input)
            }
            """,
            {"input": input_obj},
        )
        return bool(data.get("variableUpsert"))

    def variable_delete(
        self,
        project_id: str,
        environment_id: str,
        name: str,
        service_id: str | None = None,
    ) -> bool:
        input_obj: dict = {
            "projectId": project_id,
            "environmentId": environment_id,
            "name": name,
        }
        if service_id:
            input_obj["serviceId"] = service_id

        data = self.query(
            """
            mutation DeleteVariable($input: VariableDeleteInput!) {
                variableDelete(input: $input)
            }
            """,
            {"input": input_obj},
        )
        return bool(data.get("variableDelete"))

    # ------------------------------------------------------------------
    # Environments
    # ------------------------------------------------------------------

    def environments_list(self, project_id: str) -> list[dict]:
        data = self.query(
            """
            query GetEnvironments($id: String!) {
                project(id: $id) {
                    environments {
                        edges { node { id name } }
                    }
                }
            }
            """,
            {"id": project_id},
        )
        project = data.get("project", {})
        return [
            edge["node"]
            for edge in project.get("environments", {}).get("edges", [])
        ]

    def environment_create(self, name: str, project_id: str) -> dict:
        data = self.query(
            """
            mutation CreateEnvironment($name: String!, $projectId: String!) {
                environmentCreate(input: { name: $name, projectId: $projectId }) {
                    id
                    name
                }
            }
            """,
            {"name": name, "projectId": project_id},
        )
        return data.get("environmentCreate", {})

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------

    def deployment_logs(
        self,
        deployment_id: str,
        limit: int = 100,
        filter_text: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        data = self.query(
            """
            query GetDeploymentLogs(
                $deploymentId: String!, $limit: Int!,
                $filter: String, $startDate: DateTime, $endDate: DateTime
            ) {
                deploymentLogs(
                    deploymentId: $deploymentId,
                    limit: $limit,
                    filter: $filter,
                    startDate: $startDate,
                    endDate: $endDate
                ) {
                    message
                    severity
                    timestamp
                    tags { deploymentInstanceId serviceId environmentId projectId }
                    attributes { key value }
                }
            }
            """,
            {
                "deploymentId": deployment_id,
                "limit": limit,
                "filter": filter_text,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return data.get("deploymentLogs") or []

    def build_logs(
        self,
        deployment_id: str,
        limit: int = 100,
        filter_text: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        data = self.query(
            """
            query GetBuildLogs(
                $deploymentId: String!, $limit: Int!,
                $filter: String, $startDate: DateTime, $endDate: DateTime
            ) {
                buildLogs(
                    deploymentId: $deploymentId,
                    limit: $limit,
                    filter: $filter,
                    startDate: $startDate,
                    endDate: $endDate
                ) {
                    message
                    severity
                    timestamp
                    attributes { key value }
                }
            }
            """,
            {
                "deploymentId": deployment_id,
                "limit": limit,
                "filter": filter_text,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return data.get("buildLogs") or []

    # ------------------------------------------------------------------
    # Domains
    # ------------------------------------------------------------------

    def domains_list(self, service_id: str, environment_id: str) -> list[dict]:
        """List custom + railway domains for a service instance."""
        data = self.query(
            """
            query GetDomains($serviceId: String!, $environmentId: String!) {
                serviceInstance(serviceId: $serviceId, environmentId: $environmentId) {
                    domains {
                        customDomains {
                            id
                            domain
                            createdAt
                        }
                        serviceDomains {
                            id
                            domain
                            createdAt
                        }
                    }
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        instance = data.get("serviceInstance") or {}
        domains_block = instance.get("domains") or {}
        custom = [
            {**d, "type": "custom"}
            for d in (domains_block.get("customDomains") or [])
        ]
        service_doms = [
            {**d, "type": "railway"}
            for d in (domains_block.get("serviceDomains") or [])
        ]
        return custom + service_doms

    def custom_domain_create(
        self, domain: str, service_id: str, environment_id: str
    ) -> dict:
        data = self.query(
            """
            mutation CreateCustomDomain(
                $domain: String!, $serviceId: String!, $environmentId: String!
            ) {
                customDomainCreate(input: {
                    domain: $domain,
                    serviceId: $serviceId,
                    environmentId: $environmentId
                }) { id domain }
            }
            """,
            {"domain": domain, "serviceId": service_id, "environmentId": environment_id},
        )
        return data.get("customDomainCreate") or {}

    def custom_domain_delete(self, domain_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteCustomDomain($id: String!) {
                customDomainDelete(id: $id)
            }
            """,
            {"id": domain_id},
        )
        return bool(data.get("customDomainDelete"))

    def service_domain_create(self, service_id: str, environment_id: str) -> dict:
        data = self.query(
            """
            mutation GenerateServiceDomain(
                $serviceId: String!, $environmentId: String!
            ) {
                serviceDomainCreate(input: {
                    serviceId: $serviceId,
                    environmentId: $environmentId
                }) { id domain }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return data.get("serviceDomainCreate") or {}

    # ------------------------------------------------------------------
    # Volumes
    # ------------------------------------------------------------------

    def volumes_list(self, project_id: str) -> list[dict]:
        data = self.query(
            """
            query GetVolumes($id: String!) {
                project(id: $id) {
                    volumes {
                        edges { node { id name createdAt } }
                    }
                }
            }
            """,
            {"id": project_id},
        )
        project = data.get("project") or {}
        return [
            edge["node"]
            for edge in (project.get("volumes") or {}).get("edges", [])
        ]

    def volume_create(self, name: str, project_id: str) -> dict:
        data = self.query(
            """
            mutation CreateVolume($name: String!, $projectId: String!) {
                volumeCreate(input: { projectId: $projectId, name: $name }) {
                    id
                    name
                }
            }
            """,
            {"name": name, "projectId": project_id},
        )
        return data.get("volumeCreate") or {}

    def volume_delete(self, volume_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteVolume($id: String!) {
                volumeDelete(id: $id)
            }
            """,
            {"id": volume_id},
        )
        return bool(data.get("volumeDelete"))

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def service_metrics(
        self,
        service_id: str,
        environment_id: str,
        start_date: str | None = None,
    ) -> list[dict]:
        if not start_date:
            from datetime import datetime, timedelta, timezone
            start_date = (datetime.now(timezone.utc) - timedelta(hours=6)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        data = self.query(
            """
            query GetMetrics(
                $serviceId: String!, $environmentId: String!, $startDate: DateTime!
            ) {
                metrics(
                    measurements: [CPU_USAGE, MEMORY_USAGE_GB, NETWORK_RX_GB, NETWORK_TX_GB],
                    serviceId: $serviceId,
                    environmentId: $environmentId,
                    startDate: $startDate,
                    sampleRateSeconds: 3600
                ) { measurement values { ts value } }
            }
            """,
            {
                "serviceId": service_id,
                "environmentId": environment_id,
                "startDate": start_date,
            },
        )
        return data.get("metrics") or []

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def templates_list(self) -> list[dict]:
        data = self.query(
            """
            query {
                templates {
                    edges {
                        node { id code name description }
                    }
                }
            }
            """
        )
        return [
            edge["node"]
            for edge in (data.get("templates") or {}).get("edges", [])
        ]

    def template_deploy(self, code: str, project_id: str) -> dict:
        data = self.query(
            """
            mutation DeployTemplate($code: String!, $projectId: String!) {
                templateDeploy(input: { code: $code, projectId: $projectId }) {
                    projectId
                }
            }
            """,
            {"code": code, "projectId": project_id},
        )
        return data.get("templateDeploy") or {}

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def deployment_rollback(self, deployment_id: str) -> bool:
        data = self.query(
            """
            mutation RollbackDeployment($id: String!) {
                deploymentRollback(id: $id)
            }
            """,
            {"id": deployment_id},
        )
        return bool(data.get("deploymentRollback"))

    # ------------------------------------------------------------------
    # Service configuration
    # ------------------------------------------------------------------

    def service_instance_get(self, service_id: str, environment_id: str) -> dict:
        data = self.query(
            """
            query GetServiceInstance($serviceId: String!, $environmentId: String!) {
                serviceInstance(serviceId: $serviceId, environmentId: $environmentId) {
                    startCommand
                    buildCommand
                    dockerfilePath
                    healthcheckPath
                    restartPolicyType
                    rootDirectory
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return data.get("serviceInstance") or {}

    def service_instance_update(
        self, service_id: str, environment_id: str, input_obj: dict
    ) -> bool:
        data = self.query(
            """
            mutation UpdateServiceInstance(
                $serviceId: String!, $environmentId: String!,
                $input: ServiceInstanceUpdateInput!
            ) {
                serviceInstanceUpdate(
                    serviceId: $serviceId,
                    environmentId: $environmentId,
                    input: $input
                )
            }
            """,
            {
                "serviceId": service_id,
                "environmentId": environment_id,
                "input": input_obj,
            },
        )
        return bool(data.get("serviceInstanceUpdate"))

    # ------------------------------------------------------------------
    # TCP Proxies
    # ------------------------------------------------------------------

    def tcp_proxies_list(self, service_id: str, environment_id: str) -> list[dict]:
        data = self.query(
            """
            query GetTcpProxies($serviceId: String!, $environmentId: String!) {
                tcpProxies(serviceId: $serviceId, environmentId: $environmentId) {
                    id
                    applicationPort
                    proxyPort
                    domain
                    createdAt
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return data.get("tcpProxies") or []

    def tcp_proxy_create(
        self, service_id: str, environment_id: str, application_port: int
    ) -> dict:
        data = self.query(
            """
            mutation CreateTcpProxy(
                $serviceId: String!, $environmentId: String!, $applicationPort: Int!
            ) {
                tcpProxyCreate(input: {
                    serviceId: $serviceId,
                    environmentId: $environmentId,
                    applicationPort: $applicationPort
                }) { id proxyPort domain }
            }
            """,
            {
                "serviceId": service_id,
                "environmentId": environment_id,
                "applicationPort": application_port,
            },
        )
        return data.get("tcpProxyCreate") or {}

    def tcp_proxy_delete(self, proxy_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteTcpProxy($id: String!) {
                tcpProxyDelete(id: $id)
            }
            """,
            {"id": proxy_id},
        )
        return bool(data.get("tcpProxyDelete"))

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------

    def webhooks_list(self, project_id: str) -> list[dict]:
        data = self.query(
            """
            query GetWebhooks($id: String!) {
                project(id: $id) {
                    webhooks {
                        edges { node { id url } }
                    }
                }
            }
            """,
            {"id": project_id},
        )
        project = data.get("project") or {}
        return [
            edge["node"]
            for edge in (project.get("webhooks") or {}).get("edges", [])
        ]

    def webhook_create(self, url: str, project_id: str) -> dict:
        data = self.query(
            """
            mutation CreateWebhook($url: String!, $projectId: String!) {
                projectWebhookCreate(input: { projectId: $projectId, url: $url }) {
                    id
                    url
                }
            }
            """,
            {"url": url, "projectId": project_id},
        )
        return data.get("projectWebhookCreate") or {}

    def webhook_delete(self, webhook_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteWebhook($id: String!) {
                projectWebhookDelete(id: $id)
            }
            """,
            {"id": webhook_id},
        )
        return bool(data.get("projectWebhookDelete"))

    # ------------------------------------------------------------------
    # Team / Members
    # ------------------------------------------------------------------

    def team_list(self) -> list[dict]:
        """Return workspace members (replaces deprecated teams API)."""
        data = self.query(
            """
            query {
                me {
                    workspaces {
                        id
                        name
                        members { id email role }
                    }
                }
            }
            """
        )
        me = data.get("me") or {}
        workspaces = me.get("workspaces") or []
        result = []
        for ws in workspaces:
            for m in ws.get("members") or []:
                result.append(
                    {
                        **m,
                        "workspaceId": ws.get("id"),
                        "workspaceName": ws.get("name"),
                    }
                )
        return result

    def team_invite(self, workspace_id: str, email: str, role: str) -> bool:
        data = self.query(
            """
            mutation InviteWorkspaceMember(
                $workspaceId: String!, $email: String!, $role: WorkspaceRole!
            ) {
                workspaceUserInvite(
                    id: $workspaceId,
                    input: { email: $email, role: $role }
                )
            }
            """,
            {"workspaceId": workspace_id, "email": email, "role": role},
        )
        return bool(data.get("workspaceUserInvite"))

    def team_member_remove(self, workspace_id: str, user_id: str) -> bool:
        data = self.query(
            """
            mutation RemoveWorkspaceMember($workspaceId: String!, $userId: String!) {
                workspaceUserRemove(id: $workspaceId, userId: $userId)
            }
            """,
            {"workspaceId": workspace_id, "userId": user_id},
        )
        return bool(data.get("workspaceUserRemove"))

    # ------------------------------------------------------------------
    # Cron services
    # ------------------------------------------------------------------

    def service_create_cron(
        self, name: str, project_id: str, cron_schedule: str
    ) -> dict:
        data = self.query(
            """
            mutation CreateCronService(
                $name: String!, $projectId: String!, $cronSchedule: String!
            ) {
                serviceCreate(input: {
                    projectId: $projectId,
                    name: $name,
                    cronSchedule: $cronSchedule
                }) { id name }
            }
            """,
            {
                "name": name,
                "projectId": project_id,
                "cronSchedule": cron_schedule,
            },
        )
        return data.get("serviceCreate") or {}

    # ------------------------------------------------------------------
    # Private networking
    # ------------------------------------------------------------------

    def networking_list(self, environment_id: str) -> list[dict]:
        """Return all private network endpoints for an environment."""
        data = self.query(
            """
            query GetNetworking($environmentId: String!) {
                privateNetworks(environmentId: $environmentId) {
                    name
                    dnsName
                    networkId
                    publicId
                    projectId
                    environmentId
                    createdAt
                }
            }
            """,
            {"environmentId": environment_id},
        )
        return data.get("privateNetworks") or []

    # ------------------------------------------------------------------
    # Git integration
    # ------------------------------------------------------------------

    def git_connect(self, service_id: str, repo: str, branch: str) -> bool:
        data = self.query(
            """
            mutation GitConnect(
                $id: String!, $repo: String!, $branch: String!
            ) {
                serviceConnect(id: $id, input: {
                    source: { repo: $repo, branch: $branch }
                })
            }
            """,
            {"id": service_id, "repo": repo, "branch": branch},
        )
        return bool(data.get("serviceConnect"))

    def git_disconnect(self, service_id: str) -> bool:
        data = self.query(
            """
            mutation GitDisconnect($id: String!) {
                serviceDisconnect(id: $id)
            }
            """,
            {"id": service_id},
        )
        return bool(data.get("serviceDisconnect"))

    # ------------------------------------------------------------------
    # Project mutations (update / delete)
    # ------------------------------------------------------------------

    def project_update(self, project_id: str, name: str | None = None, description: str | None = None) -> dict:
        input_obj: dict = {}
        if name is not None:
            input_obj["name"] = name
        if description is not None:
            input_obj["description"] = description
        data = self.query(
            """
            mutation UpdateProject($id: String!, $input: ProjectUpdateInput!) {
                projectUpdate(id: $id, input: $input) {
                    id
                    name
                    description
                }
            }
            """,
            {"id": project_id, "input": input_obj},
        )
        return data.get("projectUpdate") or {}

    def project_delete(self, project_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteProject($id: String!) {
                projectDelete(id: $id)
            }
            """,
            {"id": project_id},
        )
        return bool(data.get("projectDelete"))

    # ------------------------------------------------------------------
    # Service mutations (create generic / update / delete)
    # ------------------------------------------------------------------

    def service_create(self, name: str, project_id: str) -> dict:
        data = self.query(
            """
            mutation CreateService($name: String!, $projectId: String!) {
                serviceCreate(input: { projectId: $projectId, name: $name }) {
                    id
                    name
                }
            }
            """,
            {"name": name, "projectId": project_id},
        )
        return data.get("serviceCreate") or {}

    def service_update(self, service_id: str, name: str | None = None) -> dict:
        input_obj: dict = {}
        if name is not None:
            input_obj["name"] = name
        data = self.query(
            """
            mutation UpdateService($id: String!, $input: ServiceUpdateInput!) {
                serviceUpdate(id: $id, input: $input) {
                    id
                    name
                }
            }
            """,
            {"id": service_id, "input": input_obj},
        )
        return data.get("serviceUpdate") or {}

    def service_delete(self, service_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteService($id: String!) {
                serviceDelete(id: $id)
            }
            """,
            {"id": service_id},
        )
        return bool(data.get("serviceDelete"))

    # ------------------------------------------------------------------
    # Deployment mutations (restart / cancel / stop)
    # ------------------------------------------------------------------

    def deployment_restart(self, deployment_id: str) -> bool:
        data = self.query(
            """
            mutation RestartDeployment($id: String!) {
                deploymentRestart(id: $id)
            }
            """,
            {"id": deployment_id},
        )
        return bool(data.get("deploymentRestart"))

    def deployment_cancel(self, deployment_id: str) -> bool:
        data = self.query(
            """
            mutation CancelDeployment($id: String!) {
                deploymentCancel(id: $id)
            }
            """,
            {"id": deployment_id},
        )
        return bool(data.get("deploymentCancel"))

    def deployment_stop(self, service_id: str, environment_id: str) -> bool:
        data = self.query(
            """
            mutation StopDeployment($serviceId: String!, $environmentId: String!) {
                deploymentStop(input: {
                    serviceId: $serviceId,
                    environmentId: $environmentId
                })
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return bool(data.get("deploymentStop"))

    # ------------------------------------------------------------------
    # Environment mutations (delete / rename)
    # ------------------------------------------------------------------

    def environment_delete(self, environment_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteEnvironment($id: String!) {
                environmentDelete(id: $id)
            }
            """,
            {"id": environment_id},
        )
        return bool(data.get("environmentDelete"))

    def environment_rename(self, environment_id: str, name: str) -> bool:
        data = self.query(
            """
            mutation RenameEnvironment($id: String!, $name: String!) {
                environmentRename(id: $id, input: { name: $name })
            }
            """,
            {"id": environment_id, "name": name},
        )
        return bool(data.get("environmentRename"))

    # ------------------------------------------------------------------
    # Bulk variables
    # ------------------------------------------------------------------

    def variable_collection_upsert(
        self,
        project_id: str,
        environment_id: str,
        variables: dict[str, str],
        service_id: str | None = None,
    ) -> bool:
        input_obj: dict = {
            "projectId": project_id,
            "environmentId": environment_id,
            "variables": variables,
        }
        if service_id:
            input_obj["serviceId"] = service_id

        data = self.query(
            """
            mutation BulkUpsertVariables($input: VariableCollectionUpsertInput!) {
                variableCollectionUpsert(input: $input)
            }
            """,
            {"input": input_obj},
        )
        return bool(data.get("variableCollectionUpsert"))

    # ------------------------------------------------------------------
    # Platform status & regions
    # ------------------------------------------------------------------

    def platform_status(self) -> dict:
        data = self.query(
            """
            query {
                platformStatus {
                    isStable
                    incident {
                        id
                        message
                        url
                        status
                    }
                }
            }
            """
        )
        return data.get("platformStatus") or {}

    def regions(self) -> list[dict]:
        data = self.query(
            """
            query {
                regions {
                    name
                    region
                    country
                    location
                    railwayMetal
                }
            }
            """
        )
        return data.get("regions") or []

    # ------------------------------------------------------------------
    # Me / User info
    # ------------------------------------------------------------------

    def me(self) -> dict:
        data = self.query(
            """
            query {
                me {
                    id
                    name
                    email
                    workspaces {
                        id
                        name
                    }
                }
            }
            """
        )
        return data.get("me") or {}

    # ------------------------------------------------------------------
    # Project members & transfer
    # ------------------------------------------------------------------

    def project_members(self, project_id: str) -> list[dict]:
        data = self.query(
            """
            query GetProjectMembers($projectId: String!) {
                projectMembers(projectId: $projectId) {
                    id
                    role
                    user { id name email }
                }
            }
            """,
            {"projectId": project_id},
        )
        return data.get("projectMembers") or []

    def project_transfer(self, project_id: str, team_id: str) -> bool:
        data = self.query(
            """
            mutation TransferProject($projectId: String!, $input: ProjectTransferInput!) {
                projectTransfer(id: $projectId, input: $input)
            }
            """,
            {"projectId": project_id, "input": {"teamId": team_id}},
        )
        return bool(data.get("projectTransfer"))

    # ------------------------------------------------------------------
    # Deployment — redeploy / remove
    # ------------------------------------------------------------------

    def deployment_trigger_v2(self, service_id: str, environment_id: str) -> dict:
        """Trigger deploy and return deployment ID."""
        data = self.query(
            """
            mutation TriggerDeployV2($serviceId: String!, $environmentId: String!) {
                serviceInstanceDeployV2(
                    serviceId: $serviceId,
                    environmentId: $environmentId
                ) { id status }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return data.get("serviceInstanceDeployV2") or {}

    def service_instance_redeploy(self, service_id: str, environment_id: str) -> bool:
        data = self.query(
            """
            mutation RedeployLatest($serviceId: String!, $environmentId: String!) {
                serviceInstanceRedeploy(
                    serviceId: $serviceId,
                    environmentId: $environmentId
                )
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return bool(data.get("serviceInstanceRedeploy"))

    def deployment_redeploy(self, deployment_id: str) -> dict:
        data = self.query(
            """
            mutation RedeployDeployment($id: String!) {
                deploymentRedeploy(id: $id) { id status }
            }
            """,
            {"id": deployment_id},
        )
        return data.get("deploymentRedeploy") or {}

    def deployment_remove(self, deployment_id: str) -> bool:
        data = self.query(
            """
            mutation RemoveDeployment($id: String!) {
                deploymentRemove(id: $id)
            }
            """,
            {"id": deployment_id},
        )
        return bool(data.get("deploymentRemove"))

    # ------------------------------------------------------------------
    # Logs — HTTP logs & environment logs
    # ------------------------------------------------------------------

    def http_logs(
        self,
        deployment_id: str,
        limit: int = 100,
        filter_text: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        data = self.query(
            """
            query GetHttpLogs(
                $deploymentId: String!, $limit: Int!,
                $filter: String, $startDate: String, $endDate: String
            ) {
                httpLogs(
                    deploymentId: $deploymentId,
                    limit: $limit,
                    filter: $filter,
                    startDate: $startDate,
                    endDate: $endDate
                ) {
                    timestamp
                    requestId
                    method
                    path
                    host
                    httpStatus
                    totalDuration
                    upstreamRqDuration
                    rxBytes
                    txBytes
                    srcIp
                    edgeRegion
                    clientUa
                    responseDetails
                    upstreamErrors
                }
            }
            """,
            {
                "deploymentId": deployment_id,
                "limit": limit,
                "filter": filter_text,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return data.get("httpLogs") or []

    def environment_logs(
        self,
        environment_id: str,
        filter_text: str | None = None,
        before_limit: int = 100,
        before_date: str | None = None,
        after_date: str | None = None,
        anchor_date: str | None = None,
        after_limit: int | None = None,
    ) -> list[dict]:
        """Fetch env-wide logs via the new schema.

        The Railway API no longer accepts ``projectId`` or ``limit``. Use
        ``beforeLimit`` (historical window) and/or ``afterLimit`` with
        ``anchorDate`` for time-anchored windows.
        """
        variables: dict = {
            "environmentId": environment_id,
            "filter": filter_text,
            "beforeLimit": before_limit,
            "beforeDate": before_date,
            "afterDate": after_date,
            "anchorDate": anchor_date,
            "afterLimit": after_limit,
        }
        data = self.query(
            """
            query GetEnvironmentLogs(
                $environmentId: String!,
                $filter: String,
                $beforeLimit: Int,
                $beforeDate: String,
                $afterDate: String,
                $anchorDate: String,
                $afterLimit: Int
            ) {
                environmentLogs(
                    environmentId: $environmentId,
                    filter: $filter,
                    beforeLimit: $beforeLimit,
                    beforeDate: $beforeDate,
                    afterDate: $afterDate,
                    anchorDate: $anchorDate,
                    afterLimit: $afterLimit
                ) {
                    message
                    severity
                    timestamp
                    tags { serviceId deploymentId deploymentInstanceId projectId environmentId }
                    attributes { key value }
                }
            }
            """,
            variables,
        )
        return data.get("environmentLogs") or []

    # ------------------------------------------------------------------
    # Domains — check, DNS status, update, delete railway domain
    # ------------------------------------------------------------------

    def custom_domain_available(self, domain: str) -> dict:
        data = self.query(
            """
            query CheckDomain($domain: String!) {
                customDomainAvailable(domain: $domain) {
                    available
                    message
                }
            }
            """,
            {"domain": domain},
        )
        return data.get("customDomainAvailable") or {}

    def custom_domain_status(self, domain_id: str, project_id: str) -> dict:
        data = self.query(
            """
            query GetDomainStatus($id: String!, $projectId: String!) {
                customDomain(id: $id, projectId: $projectId) {
                    id
                    domain
                    status {
                        dnsRecords { hostlabel requiredValue currentValue status }
                        certificateStatus
                    }
                }
            }
            """,
            {"id": domain_id, "projectId": project_id},
        )
        return data.get("customDomain") or {}

    def custom_domain_update(
        self, domain_id: str, environment_id: str, target_port: int
    ) -> bool:
        data = self.query(
            """
            mutation UpdateCustomDomain(
                $id: String!, $environmentId: String!, $targetPort: Int!
            ) {
                customDomainUpdate(
                    id: $id,
                    input: { environmentId: $environmentId, targetPort: $targetPort }
                )
            }
            """,
            {"id": domain_id, "environmentId": environment_id, "targetPort": target_port},
        )
        return bool(data.get("customDomainUpdate"))

    def service_domain_delete(self, domain_id: str) -> bool:
        data = self.query(
            """
            mutation DeleteServiceDomain($id: String!) {
                serviceDomainDelete(id: $id)
            }
            """,
            {"id": domain_id},
        )
        return bool(data.get("serviceDomainDelete"))

    # ------------------------------------------------------------------
    # Variables — resolved at deploy time
    # ------------------------------------------------------------------

    def variables_resolved(
        self, project_id: str, environment_id: str, service_id: str
    ) -> dict:
        data = self.query(
            """
            query GetResolvedVars(
                $projectId: String!, $environmentId: String!, $serviceId: String!
            ) {
                variablesForServiceDeployment(
                    projectId: $projectId,
                    environmentId: $environmentId,
                    serviceId: $serviceId
                )
            }
            """,
            {
                "projectId": project_id,
                "environmentId": environment_id,
                "serviceId": service_id,
            },
        )
        return data.get("variablesForServiceDeployment") or {}

    # ------------------------------------------------------------------
    # Volumes — update, mount, backups
    # ------------------------------------------------------------------

    def volume_update(self, volume_id: str, name: str) -> bool:
        data = self.query(
            """
            mutation UpdateVolume($volumeId: String!, $input: VolumeUpdateInput!) {
                volumeUpdate(volumeId: $volumeId, input: $input) { id name }
            }
            """,
            {"volumeId": volume_id, "input": {"name": name}},
        )
        return bool(data.get("volumeUpdate"))

    def volume_instance_update(
        self, volume_id: str, mount_path: str
    ) -> bool:
        data = self.query(
            """
            mutation UpdateVolumeInstance(
                $volumeId: String!, $input: VolumeInstanceUpdateInput!
            ) {
                volumeInstanceUpdate(volumeId: $volumeId, input: $input)
            }
            """,
            {"volumeId": volume_id, "input": {"mountPath": mount_path}},
        )
        return bool(data.get("volumeInstanceUpdate"))

    def volume_instance_info(self, volume_instance_id: str) -> dict:
        data = self.query(
            """
            query GetVolumeInstance($id: String!) {
                volumeInstance(id: $id) {
                    id
                    mountPath
                    currentSizeMB
                    state
                    volume { id name }
                    serviceInstance { serviceName }
                }
            }
            """,
            {"id": volume_instance_id},
        )
        return data.get("volumeInstance") or {}

    def volume_backup_list(self, volume_instance_id: str) -> list[dict]:
        data = self.query(
            """
            query GetVolumeBackups($volumeInstanceId: String!) {
                volumeInstanceBackupList(volumeInstanceId: $volumeInstanceId) {
                    id
                    name
                    createdAt
                    expiresAt
                    usedMB
                    referencedMB
                }
            }
            """,
            {"volumeInstanceId": volume_instance_id},
        )
        return data.get("volumeInstanceBackupList") or []

    def volume_backup_create(self, volume_instance_id: str) -> dict:
        data = self.query(
            """
            mutation CreateVolumeBackup($volumeInstanceId: String!) {
                volumeInstanceBackupCreate(volumeInstanceId: $volumeInstanceId)
            }
            """,
            {"volumeInstanceId": volume_instance_id},
        )
        return data.get("volumeInstanceBackupCreate") or {}

    def volume_backup_restore(
        self, backup_id: str, volume_instance_id: str
    ) -> bool:
        data = self.query(
            """
            mutation RestoreVolumeBackup(
                $volumeInstanceBackupId: String!, $volumeInstanceId: String!
            ) {
                volumeInstanceBackupRestore(
                    volumeInstanceBackupId: $volumeInstanceBackupId,
                    volumeInstanceId: $volumeInstanceId
                )
            }
            """,
            {
                "volumeInstanceBackupId": backup_id,
                "volumeInstanceId": volume_instance_id,
            },
        )
        return bool(data.get("volumeInstanceBackupRestore"))

    def volume_backup_delete(
        self, backup_id: str, volume_instance_id: str
    ) -> bool:
        data = self.query(
            """
            mutation DeleteVolumeBackup(
                $volumeInstanceBackupId: String!, $volumeInstanceId: String!
            ) {
                volumeInstanceBackupDelete(
                    volumeInstanceBackupId: $volumeInstanceBackupId,
                    volumeInstanceId: $volumeInstanceId
                )
            }
            """,
            {
                "volumeInstanceBackupId": backup_id,
                "volumeInstanceId": volume_instance_id,
            },
        )
        return bool(data.get("volumeInstanceBackupDelete"))

    # ------------------------------------------------------------------
    # Environments — info, staged changes
    # ------------------------------------------------------------------

    def environment_info(self, environment_id: str) -> dict:
        data = self.query(
            """
            query GetEnvironment($id: String!) {
                environment(id: $id) {
                    id
                    name
                    createdAt
                    serviceInstances {
                        edges {
                            node {
                                serviceId
                                latestDeployment { id status createdAt }
                            }
                        }
                    }
                }
            }
            """,
            {"id": environment_id},
        )
        return data.get("environment") or {}

    def environment_staged_changes(self, environment_id: str) -> list[dict]:
        data = self.query(
            """
            query GetStagedChanges($id: String!) {
                environmentStagedChanges(environmentId: $id) {
                    serviceId
                    variableChanges {
                        name
                        oldValue
                        newValue
                        action
                    }
                }
            }
            """,
            {"id": environment_id},
        )
        return data.get("environmentStagedChanges") or []

    # ------------------------------------------------------------------
    # Service instance limits
    # ------------------------------------------------------------------

    def service_instance_limits(self, service_id: str, environment_id: str) -> dict:
        data = self.query(
            """
            query GetServiceInstanceLimits($serviceId: String!, $environmentId: String!) {
                serviceInstanceLimits(
                    serviceId: $serviceId,
                    environmentId: $environmentId
                )
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return data.get("serviceInstanceLimits") or {}
