
echo[$(date)]:"START"
echo[$(date)]:"CREATING ENV"
conda create --prefix ./env python=3.8 -y
echo[$(date)]:"ACTIVATING THE ENV"
source activate ./env
echo[$(date)]:"INSTALLING THE DEV REQUIREMENTS"
pip install -r requirements_dev.txt
echo[$(date)]:"END"