%define name moin
%define version 1.2.4
%define release 1

Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
Summary:        MoinMoin Wiki engine

Group:          Applications/Internet
License:        GPL
URL:            http://moinmoin.wikiwikiweb.de
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArchitectures: noarch
BuildRequires:  python-devel
Requires:       python >= 2.2.2

%description

A WikiWikiWeb is a collaborative hypertext environment, with an
emphasis on easy access to and modification of information. MoinMoin
is a Python WikiClone that allows you to easily set up your own wiki,
only requiring a Python installation. 

%prep
%setup

%build
# replace python by python2 if python refers to version 1.5 on your system
python setup.py build

%install
# replace python by python2 if python refers to version 1.5 on your system
python setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc  README CHANGES COPYING INSTALL.html UPDATE.html

%changelog
* Fri Mar 05 2004 Florian Festi
- Initial RPM release.

