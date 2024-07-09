mkdir temp
mkdir static/uploads
sudo su -c "sudo cp tbrc_project_status_view.service /etc/systemd/system/"
sudo su -c "sudo cp tbrc_project_status_view_backup.service /etc/systemd/system/"
sudo su -c "sudo cp tbrc_project_status_view_nginx.conf /etc/nginx/sites-enabled/"
sudo su -c "sudo echo 'Init' > /var/log/tbrc_project_status_view.log"
sudo su -c "sudo chown akuro /var/log/tbrc_project_status_view.log"