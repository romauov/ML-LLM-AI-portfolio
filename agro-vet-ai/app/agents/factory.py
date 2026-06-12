def get_agent(model=None, dialog_history=None, **kwargs):
    if model == "INLINE Vet-bot Test":
        from app.agents.router_v2.agent import TopicRouterAgent
    else:
        from app.agents.router.agent import TopicRouterAgent
    return TopicRouterAgent(dialog_history=dialog_history, **kwargs)
