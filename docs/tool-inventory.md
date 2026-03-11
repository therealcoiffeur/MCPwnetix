# Acunetix MCP Tool Inventory

Generated from the embedded Acunetix API snapshot.

| Tool name | Purpose | Mapped Acunetix endpoint(s) | Required inputs | Side effects |
| --- | --- | --- | --- | --- |
| abort_scan | Abort Scan | `POST /scans/{scan_id}/abort` | scan_id | High impact. Changes scanner state or mutates existing resources. |
| add_role_mappings_to_user_group | Add Role Mappings to a User Group | `POST /user_groups/{user_group_id}/roles` | body, user_group_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| add_target | Create Target | `POST /targets` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| add_targets | Creates multiple targets | `POST /targets/add` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| add_user | User | `POST /users` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| add_users_to_user_group | Add Users to a User Group | `POST /user_groups/{user_group_id}/users` | body, user_group_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| agents_generate_registration_token | Generate or regenerate Token | `POST /config/agents/registration_token` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| agents_get_registration_token | Registration Token | `GET /config/agents/registration_token` | None | None. Read-only operation. |
| agents_remove_registration_token | Registration Token | `DELETE /config/agents/registration_token` | None | Destructive. Deletes or detaches Acunetix resources. |
| assign_workers_to_target | Assign Workers to Target | `POST /targets/{target_id}/configuration/workers` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| authorize_worker | Authorize Worker | `POST /workers/{worker_id}/authorize` | body, worker_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| check_worker | Check Worker connection | `POST /workers/{worker_id}/check` | body, worker_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| configure_target | Target Configuration | `PATCH /targets/{target_id}/configuration` | target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| create_excluded_hours_profile | Create Excluded Hours Profile | `POST /excluded_hours_profiles` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| create_issue_tracker_entry | Create Issue Tracker | `POST /issue_trackers` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| create_role | Roles | `POST /roles` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| create_scanning_profile | Create Scan Type (Scanning Profile) | `POST /scanning_profiles` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| create_user_group | User Groups | `POST /user_groups` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| create_vulnerability_issues | Schedules the creation of issues on issue tracker. | `POST /vulnerabilities/issues` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| create_waf_entry | Create a WAF | `POST /wafs` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| delete_issue_tracker_entry | Delete Issue Tracker entry | `DELETE /issue_trackers/{issue_tracker_id}` | issue_tracker_id | Destructive. Deletes or detaches Acunetix resources. |
| delete_scanning_profile | Scan Type (Scanning Profile) | `DELETE /scanning_profiles/{scanning_profile_id}` | scanning_profile_id | Destructive. Deletes or detaches Acunetix resources. |
| delete_waf_entry | Delete WAF entry | `DELETE /wafs/{waf_id}` | waf_id | Destructive. Deletes or detaches Acunetix resources. |
| delete_worker | Worker | `DELETE /workers/{worker_id}` | worker_id | Destructive. Deletes or detaches Acunetix resources. |
| delete_worker_ignore_errors | Worker | `DELETE /workers/{worker_id}/ignore_errors` | worker_id | Destructive. Deletes or detaches Acunetix resources. |
| disable_users | Disable Users | `POST /users/disable` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| download_report | download_report | `GET /reports/download/{descriptor}` | descriptor | None. Read-only operation. |
| enable_users | Enable Users | `POST /users/enable` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| generate_new_report | Reports | `POST /reports` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| get_continuous_scans | List Target Continuous Scans | `GET /targets/{target_id}/continuous_scan/list` | target_id | None. Read-only operation. |
| get_excluded_hours_profile | Excluded Hours Profile | `GET /excluded_hours_profiles/{excluded_hours_id}` | excluded_hours_id | None. Read-only operation. |
| get_excluded_hours_profiles | Excluded Hours Profiles | `GET /excluded_hours_profiles` | None | None. Read-only operation. |
| get_issue_tracker_entry | Issue Tracker details | `GET /issue_trackers/{issue_tracker_id}` | issue_tracker_id | None. Read-only operation. |
| get_issue_trackers | Issue Trackers | `GET /issue_trackers` | None | None. Read-only operation. |
| get_report | Report | `GET /reports/{report_id}` | report_id | None. Read-only operation. |
| get_report_templates | Report Templates | `GET /report_templates` | None | None. Read-only operation. |
| get_reports | Reports | `GET /reports` | None | None. Read-only operation. |
| get_role | Role | `GET /roles/{role_id}` | role_id | None. Read-only operation. |
| get_roles | Roles | `GET /roles` | None | None. Read-only operation. |
| get_scan | Scan | `GET /scans/{scan_id}` | scan_id | None. Read-only operation. |
| get_scan_result | Scan Result | `GET /results/{result_id}` | result_id | None. Read-only operation. |
| get_scan_result_history | Scan Results | `GET /scans/{scan_id}/results` | scan_id | None. Read-only operation. |
| get_scanning_profile | Scan Type (Scanning Profile) | `GET /scanning_profiles/{scanning_profile_id}` | scanning_profile_id | None. Read-only operation. |
| get_scanning_profiles | Scan Types (Scanning Profiles) | `GET /scanning_profiles` | None | None. Read-only operation. |
| get_scans | Scans | `GET /scans` | None | None. Read-only operation. |
| get_target | Target | `GET /targets/{target_id}` | target_id | None. Read-only operation. |
| get_target_configuration | Target Configuration | `GET /targets/{target_id}/configuration` | target_id | None. Read-only operation. |
| get_targets | Targets | `GET /targets` | None | None. Read-only operation. |
| get_user | User | `GET /users/{user_id}` | user_id | None. Read-only operation. |
| get_user_group | User Group | `GET /user_groups/{user_group_id}` | user_group_id | None. Read-only operation. |
| get_user_group_role_mappings | List all Role Mappings for the User Group | `GET /user_groups/{user_group_id}/roles` | user_group_id | None. Read-only operation. |
| get_user_groups | User Groups | `GET /user_groups` | None | None. Read-only operation. |
| get_users | Users | `GET /users` | None | None. Read-only operation. |
| get_vulnerabilities | Vulnerabilities | `GET /vulnerabilities` | None | None. Read-only operation. |
| get_vulnerability_details | Vulnerability | `GET /vulnerabilities/{vuln_id}` | vuln_id | None. Read-only operation. |
| get_vulnerability_groups | get_vulnerability_groups | `GET /vulnerability_groups` | None | None. Read-only operation. |
| get_vulnerability_http_response | Vulnerability | `GET /vulnerabilities/{vuln_id}/http_response` | vuln_id | None. Read-only operation. |
| get_vulnerability_type | Vulnerability Type | `GET /vulnerability_types/{vt_id}` | vt_id | None. Read-only operation. |
| get_vulnerability_types | Vulnerability Types | `GET /vulnerability_types` | None | None. Read-only operation. |
| get_waf_entry | WAF details | `GET /wafs/{waf_id}` | waf_id | None. Read-only operation. |
| get_wafs | WAFs | `GET /wafs` | None | None. Read-only operation. |
| get_worker | Worker | `GET /workers/{worker_id}` | worker_id | None. Read-only operation. |
| get_workers | Workers | `GET /workers` | None | None. Read-only operation. |
| get_workers_assigned_to_target | Target assigned Workers | `GET /targets/{target_id}/configuration/workers` | target_id | None. Read-only operation. |
| issue_tracker_entry_check_connection | Issue Tracker details | `GET /issue_trackers/{issue_tracker_id}/check_connection` | issue_tracker_id | None. Read-only operation. |
| issue_tracker_entry_get_collections | Issue Tracker Collections (TFS) | `GET /issue_trackers/{issue_tracker_id}/collections` | issue_tracker_id | None. Read-only operation. |
| issue_tracker_entry_get_custom_fields | Issue Tracker Custom Fields | `GET /issue_trackers/{issue_tracker_id}/custom_fields` | issue_tracker_id | None. Read-only operation. |
| issue_tracker_entry_get_issue_types | Issue Tracker Projects | `GET /issue_trackers/{issue_tracker_id}/projects/issue_types` | issue_tracker_id, project_id | None. Read-only operation. |
| issue_tracker_entry_get_issue_types_by_project_id | Issue Tracker Projects | `GET /issue_trackers/{issue_tracker_id}/projects/{project_id}/issue_types` | issue_tracker_id, project_id | None. Read-only operation. |
| issue_tracker_entry_get_projects | Issue Tracker Projects | `GET /issue_trackers/{issue_tracker_id}/projects` | issue_tracker_id | None. Read-only operation. |
| issue_trackers_check_connection | Issue Tracker check connection | `POST /issue_trackers/check_connection` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| issue_trackers_check_issue_types | Issue Tracker Issue Types | `POST /issue_trackers/check_issue_types` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| issue_trackers_check_projects | Issue Tracker Projects | `POST /issue_trackers/check_projects` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| issue_trackers_get_collections | Issue Tracker get collections | `POST /issue_trackers/collections` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| issue_trackers_get_custom_fields | Issue Tracker get a list of custom fields | `POST /issue_trackers/custom_fields` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| list_target_groups | Target Groups including Target | `GET /targets/{target_id}/target_groups` | target_id | None. Read-only operation. |
| modify_excluded_hours_profile | Excluded Hours Profile | `PATCH /excluded_hours_profiles/{excluded_hours_id}` | body, excluded_hours_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| recheck_vulnerabilities | Re-check Vulnerability | `PUT /vulnerabilities/recheck` | body | High impact. Changes scanner state or mutates existing resources. |
| recheck_vulnerability | Re-check Vulnerability | `PUT /vulnerabilities/{vuln_id}/recheck` | body, vuln_id | High impact. Changes scanner state or mutates existing resources. |
| reject_worker | Reject Worker | `POST /workers/{worker_id}/reject` | body, worker_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| remove_excluded_hours_profile | Excluded Hours Profile | `DELETE /excluded_hours_profiles/{excluded_hours_id}` | excluded_hours_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_report | Report | `DELETE /reports/{report_id}` | report_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_reports | Delete reports | `POST /reports/delete` | body | High impact. Changes scanner state or mutates existing resources. |
| remove_role | Role | `DELETE /roles/{role_id}` | role_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_role_mappings_from_user_group | Remove Role Mappings from a User Group | `DELETE /user_groups/{user_group_id}/roles` | body, user_group_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_scan | Scan | `DELETE /scans/{scan_id}` | scan_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_target | Target | `DELETE /targets/{target_id}` | target_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_targets | Removes multiple targets | `POST /targets/delete` | body | High impact. Changes scanner state or mutates existing resources. |
| remove_user | User | `DELETE /users/{user_id}` | user_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_user_group | User Group | `DELETE /user_groups/{user_group_id}` | user_group_id | Destructive. Deletes or detaches Acunetix resources. |
| remove_users | Remove Users | `POST /users/delete` | body | High impact. Changes scanner state or mutates existing resources. |
| remove_users_from_user_group | Remove Users from a User Group | `DELETE /user_groups/{user_group_id}/users` | body, user_group_id | Destructive. Deletes or detaches Acunetix resources. |
| rename_worker | Rename Worker | `POST /workers/{worker_id}/rename` | body, worker_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| repeat_report | Re-generate Report | `POST /reports/{report_id}/repeat` | report_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| reports_export | Export | `POST /exports` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| reports_get_export | Export | `GET /exports/{export_id}` | export_id | None. Read-only operation. |
| reports_get_export_types | Export Types | `GET /export_types` | None | None. Read-only operation. |
| reports_remove_export | Export | `DELETE /exports/{export_id}` | export_id | Destructive. Deletes or detaches Acunetix resources. |
| reports_remove_exports | Delete reports | `POST /exports/delete` | body | High impact. Changes scanner state or mutates existing resources. |
| results_get_location_children | Scan Result Crawl Data Location Children | `GET /scans/{scan_id}/results/{result_id}/crawldata/{loc_id}/children` | loc_id, result_id, scan_id | None. Read-only operation. |
| results_get_location_details | Scan Result Crawl Data Location | `GET /scans/{scan_id}/results/{result_id}/crawldata/{loc_id}` | loc_id, result_id, scan_id | None. Read-only operation. |
| results_get_location_vulnerabilities | Scan Result crawl data vulnerabilities | `GET /scans/{scan_id}/results/{result_id}/crawldata/{loc_id}/vulnerabilities` | loc_id, result_id, scan_id | None. Read-only operation. |
| results_get_scan_session_vulnerability_http_response | Vulnerability | `GET /scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}/http_response` | result_id, scan_id, vuln_id | None. Read-only operation. |
| results_get_scan_technologies | Scan Result Technologies Found | `GET /scans/{scan_id}/results/{result_id}/technologies` | result_id, scan_id | None. Read-only operation. |
| results_get_scan_technology_vulnerabilities | Scan Result Technology Vulnerabilities | `GET /scans/{scan_id}/results/{result_id}/technologies/{tech_id}/locations/{loc_id}/vulnerabilities` | loc_id, result_id, scan_id, tech_id | None. Read-only operation. |
| results_get_scan_technology_vulnerabilities_2 | Technology Vulnerabilities For This Target | `GET /targets/{target_id}/technologies/{tech_id}/vulnerabilities` | target_id, tech_id | None. Read-only operation. |
| results_get_scan_vulnerabilities | Scan Result Vulnerabilities | `GET /scans/{scan_id}/results/{result_id}/vulnerabilities` | result_id, scan_id | None. Read-only operation. |
| results_get_scan_vulnerability_detail | Scan Result Vulnerability | `GET /scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}` | result_id, scan_id, vuln_id | None. Read-only operation. |
| results_get_scan_vulnerability_detail_from_vuln_id | Scan Result Vulnerability | `GET /scan_vulnerabilities/{vuln_id}` | vuln_id | None. Read-only operation. |
| results_get_scan_vulnerability_types | Scan Result Vulnerability Types | `GET /scans/{scan_id}/results/{result_id}/vulnerability_types` | result_id, scan_id | None. Read-only operation. |
| results_get_statistics | Scan Statistics | `GET /scans/{scan_id}/results/{result_id}/statistics` | result_id, scan_id | None. Read-only operation. |
| results_get_target_technologies | Latest Technologies Found On Target | `GET /targets/{target_id}/technologies` | target_id | None. Read-only operation. |
| results_recheck_scan_session_vulnerabilities | Re-check Vulnerabilities | `POST /scans/{scan_id}/results/{result_id}/vulnerabilities/recheck` | body, result_id, scan_id | High impact. Changes scanner state or mutates existing resources. |
| results_recheck_scan_session_vulnerability | Re-check Vulnerability | `PUT /scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}/recheck` | body, result_id, scan_id, vuln_id | High impact. Changes scanner state or mutates existing resources. |
| results_search_crawl_data | Scan Result Crawl Data | `GET /scans/{scan_id}/results/{result_id}/crawldata` | result_id, scan_id | None. Read-only operation. |
| results_set_scan_session_vulnerability_status | Vulnerability status | `PUT /scans/{scan_id}/results/{result_id}/vulnerabilities/{vuln_id}/status` | body, result_id, scan_id, vuln_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| resume_scan | Resume Scan | `POST /scans/{scan_id}/resume` | scan_id | High impact. Changes scanner state or mutates existing resources. |
| roles_get_permissions | Permissions | `GET /roles/permissions` | None | None. Read-only operation. |
| schedule_scan | Schedule Scan | `POST /scans` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| set_vulnerability_status | Vulnerability status | `PUT /vulnerabilities/{vuln_id}/status` | body, vuln_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| target_groups_add_group | Create Target Group | `POST /target_groups` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
| target_groups_change_group | Target Group | `PATCH /target_groups/{group_id}` | body, group_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| target_groups_change_targets | Targets in Target Group | `PATCH /target_groups/{group_id}/targets` | body, group_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| target_groups_delete_group | Delete Target Group | `DELETE /target_groups/{group_id}` | group_id | Destructive. Deletes or detaches Acunetix resources. |
| target_groups_delete_groups | Target Group | `POST /target_groups/delete` | body | High impact. Changes scanner state or mutates existing resources. |
| target_groups_get_group | Target Group | `GET /target_groups/{group_id}` | group_id | None. Read-only operation. |
| target_groups_get_groups | Target Groups | `GET /target_groups` | None | None. Read-only operation. |
| target_groups_list_targets | Targets in Target Group | `GET /target_groups/{group_id}/targets` | group_id | None. Read-only operation. |
| target_groups_set_targets | Assign Targets to Target Group | `POST /target_groups/{group_id}/targets` | body, group_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| targets_add_allowed_host | Target Allowed Hosts | `POST /targets/{target_id}/allowed_hosts` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| targets_cvs_export | Targets CVS Export | `GET /targets/cvs_export` | None | None. Read-only operation. |
| targets_delete_client_certificate | Target Client Certificate | `DELETE /targets/{target_id}/configuration/client_certificate` | target_id | Destructive. Deletes or detaches Acunetix resources. |
| targets_delete_imported_file | Target Import | `DELETE /targets/{target_id}/configuration/imports/{import_id}` | import_id, target_id | Destructive. Deletes or detaches Acunetix resources. |
| targets_delete_login_sequence | Target Login Sequence | `DELETE /targets/{target_id}/configuration/login_sequence` | target_id | Destructive. Deletes or detaches Acunetix resources. |
| targets_download_login_sequence | Target Login Sequence download | `GET /targets/{target_id}/configuration/login_sequence/download` | target_id | None. Read-only operation. |
| targets_download_sensor | Target AcuSensor download | `GET /targets/sensors/{sensor_type}/{sensor_secret}` | sensor_secret, sensor_type | None. Read-only operation. |
| targets_get_allowed_hosts | Target Allowed Hosts | `GET /targets/{target_id}/allowed_hosts` | target_id | None. Read-only operation. |
| targets_get_client_certificate | Target Client Certificate | `GET /targets/{target_id}/configuration/client_certificate` | target_id | None. Read-only operation. |
| targets_get_continuous_scan_status | Target Continuous Scan status | `GET /targets/{target_id}/continuous_scan` | target_id | None. Read-only operation. |
| targets_get_excluded_paths | Get target excluded path | `GET /targets/{target_id}/configuration/exclusions` | target_id | None. Read-only operation. |
| targets_get_imported_files | Target Import | `GET /targets/{target_id}/configuration/imports` | target_id | None. Read-only operation. |
| targets_get_login_sequence | Target Login Sequence | `GET /targets/{target_id}/configuration/login_sequence` | target_id | None. Read-only operation. |
| targets_remove_allowed_host | Target Allowed Host | `DELETE /targets/{target_id}/allowed_hosts/{allowed_target_id}` | allowed_target_id, target_id | Destructive. Deletes or detaches Acunetix resources. |
| targets_reset_sensor_secret | Target AcuSensor reset secret | `POST /targets/{target_id}/sensor/reset` | body, target_id | High impact. Changes scanner state or mutates existing resources. |
| targets_set_client_certificate | Target Client Certificate | `POST /targets/{target_id}/configuration/client_certificate` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| targets_set_continuous_scan_status | Continuous Scan status | `POST /targets/{target_id}/continuous_scan` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| targets_set_login_sequence | Target Login Sequence | `POST /targets/{target_id}/configuration/login_sequence` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| targets_update_excluded_paths | Update target excuded list | `POST /targets/{target_id}/configuration/exclusions` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| targets_upload_import_file | Target Import | `POST /targets/{target_id}/configuration/imports` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| trigger_scan | Trigger Scan a new scan session | `POST /scans/{scan_id}/trigger` | scan_id | High impact. Changes scanner state or mutates existing resources. |
| update_issue_tracker_entry | Issue Tracker | `PATCH /issue_trackers/{issue_tracker_id}` | body, issue_tracker_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| update_role | Role | `PATCH /roles/{role_id}` | body, role_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| update_scan | Scan | `PATCH /scans/{scan_id}` | body, scan_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| update_scanning_profile | Scan Type (Scanning Profile) | `PATCH /scanning_profiles/{scanning_profile_id}` | body, scanning_profile_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| update_target | Target | `PATCH /targets/{target_id}` | body, target_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| update_user | User | `PATCH /users/{user_id}` | body, user_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| update_user_group | User Group | `PATCH /user_groups/{user_group_id}` | body, user_group_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| update_waf_entry | WAF | `PATCH /wafs/{waf_id}` | body, waf_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| upgrade_worker | Upgrade Worker | `POST /workers/{worker_id}/upgrade` | body, worker_id | Mutating. Creates, updates, launches, or reconfigures resources. |
| waf_entry_check_connection | WAF connection | `GET /wafs/{waf_id}/check_connection` | waf_id | None. Read-only operation. |
| wafs_check_connection | WAF check connection | `POST /wafs/check_connection` | body | Mutating. Creates, updates, launches, or reconfigures resources. |
