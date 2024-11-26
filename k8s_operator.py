import kubernetes as k8s
import urllib3

urllib3.disable_warnings()


class K8sOperator:

    def __init__(self):
        k8s.config.load_kube_config(config_file="/root/.kube/config")
        self.k8s_core_api = k8s.client.CoreV1Api()
        self.k8s_apps_api = k8s.client.AppsV1Api()

    def get_deployment_instance(self, deployment_name, namespace):
        response = self.k8s_apps_api.list_namespaced_deployment(namespace)
        for instance in response.items:
            if instance.metadata.name == deployment_name:
                return instance
        return None

    def scale_deployment_instance(self, deployment_instance, replicas):
        deployment_instance.spec.replicas = replicas
        response = self.k8s_apps_api.patch_namespaced_deployment(
            deployment_instance.metadata.name,
            deployment_instance.metadata.namespace,
            deployment_instance
        )
        return response

    def scale_deployment_by_replicas(self, deployment_name, replicas, namespace="default"):
        instance = self.get_deployment_instance(deployment_name, namespace)
        if instance is None:
            print(f"Error: Deployment {deployment_name} not found")
            return None
        return self.scale_deployment_instance(instance, replicas)
    
    def get_deployment_replicas(self, deployment_name, namespace="default"):
        response = self.k8s_apps_api.read_namespaced_deployment_scale(deployment_name, namespace)
        return response.spec.replicas

if __name__ == "__main__":

    deployment_name = "cartservice"
    changed_replicas = 4

    operator = K8sOperator()
    replicas = operator.get_deployment_replicas(deployment_name)
    print(f"Now {deployment_name} replicas is {replicas}")
    response = operator.scale_deployment_by_replicas(deployment_name, changed_replicas)
    if response is not None:
        print(f"Exec result: {response.spec.replicas}")
