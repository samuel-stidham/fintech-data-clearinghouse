def notify_external_services(alert_data):
    """
    Dummy method to handle external notifications.
    NOT IMPLEMENTED.
    """
    severity = alert_data.get('severity', 'INFO')
    
    # Logic for Slack
    # if severity == 'WARNING':
    #     slack_client.post_message(channel="#compliance", text=alert_data['description'])
    
    # Logic for PagerDuty
    # if severity == 'CRITICAL':
    #     pagerduty.trigger_incident(
    #         title=f"Compliance Breach: {alert_data['account']}",
    #         details=alert_data
    #     )
    
    pass