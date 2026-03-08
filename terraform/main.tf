terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "iot-gateway-rg-psdtopicy"
  location = "eastasia" # Changed to a universally allowed region
}

# 2. Azure Kubernetes Service (AKS) Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "iot-gateway-aks-psdtopicy"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "iotgateway"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_B2s_v2" # Updated to an allowed v2 size
  }

  identity {
    type = "SystemAssigned"
  }
}

# 3. Azure Database for PostgreSQL (Flexible Server)
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "iot-gateway-pg-psdtopicy"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = "14"
  administrator_login    = "tbadmin"
  administrator_password = "PsdtopicyGroup2!" 
  zone                   = "1"
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms" 
}

# Allow Azure Services (like our AKS cluster) to access the database
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "AllowAzureIPs"
  server_id        = azurerm_postgresql_flexible_server.postgres.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# 4. Azure IoT Hub (Managed MQTT Broker)
resource "azurerm_iothub" "iothub" {
  name                = "iot-gateway-hub-psdtopicy"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  sku {
    name     = "F1" # Free tier for development
    capacity = 1
  }
}