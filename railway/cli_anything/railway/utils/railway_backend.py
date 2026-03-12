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

    def deployments_list(self, service_id: str) -> list[dict]:
        data = self.query(
            """
            query GetDeployments($serviceId: String!) {
                deployments(input: { serviceId: $serviceId }) {
                    edges {
                        node {
                            id
                            status
                            createdAt
                            staticUrl
                        }
                    }
                }
            }
            """,
            {"serviceId": service_id},
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

    def deployment_logs(self, deployment_id: str, limit: int = 100) -> list[dict]:
        data = self.query(
            """
            query GetDeploymentLogs($deploymentId: String!, $limit: Int!) {
                deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
                    message
                    severity
                    timestamp
                }
            }
            """,
            {"deploymentId": deployment_id, "limit": limit},
        )
        return data.get("deploymentLogs") or []

    def build_logs(self, deployment_id: str, limit: int = 100) -> list[dict]:
        data = self.query(
            """
            query GetBuildLogs($deploymentId: String!, $limit: Int!) {
                buildLogs(deploymentId: $deploymentId, limit: $limit) {
                    message
                    severity
                    timestamp
                }
            }
            """,
            {"deploymentId": deployment_id, "limit": limit},
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

    def service_metrics(self, service_id: str, environment_id: str) -> dict:
        data = self.query(
            """
            query GetServiceMetrics($serviceId: String!, $environmentId: String!) {
                serviceMetrics(serviceId: $serviceId, environmentId: $environmentId) {
                    cpuPercentage
                    memoryUsageBytes
                    networkRxBytes
                    networkTxBytes
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        return data.get("serviceMetrics") or {}

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
                serviceInstance(serviceId: $serviceId, environmentId: $environmentId) {
                    tcpProxies {
                        edges {
                            node { id applicationPort proxyPort domain }
                        }
                    }
                }
            }
            """,
            {"serviceId": service_id, "environmentId": environment_id},
        )
        instance = data.get("serviceInstance") or {}
        return [
            edge["node"]
            for edge in (instance.get("tcpProxies") or {}).get("edges", [])
        ]

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
        """Return a list of teams with their members."""
        data = self.query(
            """
            query {
                me {
                    teams {
                        edges {
                            node {
                                id
                                name
                                members {
                                    edges {
                                        node { id email role }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
        )
        me = data.get("me") or {}
        teams = [
            edge["node"]
            for edge in (me.get("teams") or {}).get("edges", [])
        ]
        # Flatten members list for convenience
        result = []
        for team in teams:
            members = [
                {**m["node"], "teamId": team["id"], "teamName": team["name"]}
                for m in (team.get("members") or {}).get("edges", [])
            ]
            result.extend(members)
        return result

    def team_invite(self, team_id: str, email: str, role: str) -> bool:
        data = self.query(
            """
            mutation InviteTeamMember(
                $teamId: String!, $email: String!, $role: TeamMemberRole!
            ) {
                teamInvite(teamId: $teamId, email: $email, role: $role)
            }
            """,
            {"teamId": team_id, "email": email, "role": role},
        )
        return bool(data.get("teamInvite"))

    def team_member_remove(self, team_id: str, user_id: str) -> bool:
        data = self.query(
            """
            mutation RemoveTeamMember($teamId: String!, $userId: String!) {
                teamMemberRemove(teamId: $teamId, userId: $userId)
            }
            """,
            {"teamId": team_id, "userId": user_id},
        )
        return bool(data.get("teamMemberRemove"))

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

    def networking_list(self, project_id: str) -> list[dict]:
        """Return all internal domains across all service instances in a project."""
        data = self.query(
            """
            query GetNetworking($id: String!) {
                project(id: $id) {
                    services {
                        edges {
                            node {
                                id
                                name
                                serviceInstances {
                                    edges {
                                        node {
                                            domains {
                                                edges {
                                                    node { id internalDomain }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """,
            {"id": project_id},
        )
        project = data.get("project") or {}
        result = []
        for svc_edge in (project.get("services") or {}).get("edges", []):
            svc = svc_edge["node"]
            for inst_edge in (svc.get("serviceInstances") or {}).get("edges", []):
                inst = inst_edge["node"]
                for dom_edge in (inst.get("domains") or {}).get("edges", []):
                    dom = dom_edge["node"]
                    if dom.get("internalDomain"):
                        result.append(
                            {
                                "serviceId": svc.get("id"),
                                "serviceName": svc.get("name"),
                                "id": dom.get("id"),
                                "internalDomain": dom.get("internalDomain"),
                            }
                        )
        return result

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
