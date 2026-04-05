from agio.core.events import callback, AEvent
import click


@callback('pipe.publish.file_context_ready')
def print_publish_context(event: AEvent):
    click.secho('Publish file context:', fg='green')
    ctx = event.payload['context']
    print('======= PUBLISH CONTEXT ================================')
    max_width = max([len(key) for key in ctx.keys()])
    for key, value in sorted(ctx.items()):
        print(f' {key:>{max_width}} = {value!r}')
    print('========================================================')




