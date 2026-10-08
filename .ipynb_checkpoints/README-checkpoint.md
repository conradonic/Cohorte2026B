# Diplomatura ID e IA de IB

## Clase 1 

### Primeros pasos

#### Instalación de Control de Versiones - Git (Windows)

1. Descargar el instalador:

  - Ir a https://git-scm.com/install/windows y elegir la versión adecuada
  - Ejecutar el instalador. Las opciones por defecto son adecuadas


#### Instalación de vscode (opcional)

1. Descargar el instalador:
  - Ir a https://code.visualstudio.com/Download#
  - Elegir el link a, por ejemplo, "User Installer" para la plataforma deseada
  - Ejecutar el instalador
  - Aceptar términos y condiciones

2. Uso:
  - Ejecutar vscode
  - Abrir un archivo de python (o crear uno y llamarlo test.py)
    - Si ofrece instalar extensiones para Python: aceptar (sí)
    - Si ofrece instalar Python: rechazar (no)

#### Instalación de Miniconda (Windows)

Para instalar Miniconda seguimos las instrucciones en https://www.anaconda.com/docs/getting-started/miniconda/install/overview

1. Descargar el instalador:
   - Ir a https://www.anaconda.com/download 
   - Registrarse o apretar "Skip Registration"
   - Descargar Miniconda (a la derecha)

2. Instalar:
   - Ejecutar el archivo que se descargó (Setup)
   - Aceptar términos y condiciones
   - Install for: "Just me"
   - Elegir carpeta de instalación (default está bien)
   - Elegir todos las opciones excepto agregar al PATH
   
3. Verificación 
   - Ejecutar en el menú Start -> Anaconda Prompt
   
   
#### Crear el environment

Desde el "Anaconda Prompt" crear el environment del curso:

Se puede utilizar el archivo "environment.yml", ejecutando la línea

- `conda env create --file environment.yml`

o, si falla, dar el nombre explícitamente con:

- `conda env create --file environment.yml -n diplo-ia`

Alternativamente, se puede crear un environment vacío e instalar los paquetes necesarios:

- `conda env create -n diplo-ia`
- `conda activate diplo-ia`
- `conda install python ipython numpy matplotlib scipy pandas jupyter jupyterlab-git`


#### Utilizar el environment

##### Con jupyter

- Activar con `conda activate diplo-ia`
- Ejecutar `jupyter-lab`

##### Con vscode

- Después de instalar Miniconda y crear el environment. Abrir un archivo de Python (nombre.py)

- Apretar las teclas Ctrl+Shift+P (para ir a la línea de comandos) y escribir "Seleccionar Intérprete" (Select Interpreter)
	- Elegir el ejecutable Python del environment creado: "diplo-ia".
