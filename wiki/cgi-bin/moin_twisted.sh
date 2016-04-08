# -n == nodaemon - does not background itself
# better use an unpriviledged port and sudo to an unpriv. user with twisted 1.1.1
# twisted does not give up root group, even if you change uid/gid in there
sudo -u unprivuser twistd2.3 --python=moin_twisted.py -n

