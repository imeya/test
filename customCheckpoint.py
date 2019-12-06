import logging
import asyncio
import sys
import os
import signal
import functools

from azure.eventprocessorhost import (
    AbstractEventProcessor,
    AzureStorageCheckpointLeaseManager,
    EventHubConfig,
    EventProcessorHost,
    EPHOptions)


class EventProcessor(AbstractEventProcessor):    

    def __init__(self, params=None):
        """
        Init Event processor
        """
        super().__init__(params)
        self._msg_counter = 0

    async def open_async(self, context):
        """
        Called by processor host to initialize the event processor.
        """
        print("Connection established {}".format(context.partition_id))

    async def close_async(self, context, reason):
        """
        Called by processor host to indicate that the event processor is being stopped.
        :param context: Information about the partition
        :type context: ~azure.eventprocessorhost.PartitionContext
        """
        print("Connection closed (reason {}, id {}, offset {}, sq_number {})".format(
            reason,
            context.partition_id,
            context.offset,
            context.sequence_number))

    async def process_events_async(self, context, messages):
        """
        Called by the processor host when a batch of events has arrived.
        This is where the real work of the event processor is done.
        :param context: Information about the partition
        :type context: ~azure.eventprocessorhost.PartitionContext
        :param messages: The events to be processed.
        :type messages: list[~azure.eventhub.common.EventData]
        """
        #print("Events processed {}".format(context.sequence_number))
        for m in messages:
            data = m.body_as_str()
            print("Received data: {}".format(data))
        await context.checkpoint_async()
        

    async def process_error_async(self, context, error):
        """
        Called when the underlying client experiences an error while receiving.
        EventProcessorHost will take care of recovering from the error and
        continuing to pump messages,so no action is required from
        :param context: Information about the partition
        :type context: ~azure.eventprocessorhost.PartitionContext
        :param error: The error that occured.
        """
        print("Event Processor Error {!r}".format(error))


async def wait_and_close(host):
    """
    Run EventProcessorHost for 2 minutes then shutdown.
    """
    await asyncio.sleep(60)
    await host.close_async()


try:
    loop = asyncio.get_event_loop()

    # Storage Account Credentials
    STORAGE_ACCOUNT_NAME = "xxx"
    STORAGE_KEY = "xxx"
    LEASE_CONTAINER_NAME = "mytest9"

    NAMESPACE = "xxx"
    EVENTHUB = "xxx"
    USER = "RootManageSharedAccessKey"
    KEY = "xxx"

    #the format: eventhub_namespace/eventhub_name/, note that the "/" should at the end
    blob_prefix="ivanehubns/myeventhub/" 

    # Eventhub config and storage manager 
    eh_config = EventHubConfig(NAMESPACE, EVENTHUB, USER, KEY, consumer_group="$default")
    eh_options = EPHOptions()
    eh_options.release_pump_on_timeout = True
    eh_options.debug_trace = False
    storage_manager = AzureStorageCheckpointLeaseManager(
        STORAGE_ACCOUNT_NAME, STORAGE_KEY, LEASE_CONTAINER_NAME,storage_blob_prefix=blob_prefix)
    
    

    # Event loop and host
    host = EventProcessorHost(
        EventProcessor,
        eh_config,
        storage_manager,
        ep_params=["param1","param2"],
        eph_options=eh_options,
        loop=loop)

    #storage_manager.initialize(host)
    #print(storage_manager.consumer_group_directory)
    tasks = asyncio.gather(
        host.open_async(),
        wait_and_close(host))
    loop.run_until_complete(tasks)

except KeyboardInterrupt:
    # Canceling pending tasks and stopping the loop
    for task in asyncio.Task.all_tasks():
        task.cancel()
    loop.run_forever()
    tasks.exception()

finally:
    loop.stop()