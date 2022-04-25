require 'fluent/plugin/filter'

module Fluent::Plugin
  class TractorMetadataFilter < Filter
    # Register this filter as "passthru"
    Fluent::Plugin.register_filter('tractor_metadata', self)

    def filter(tag, time, record)
      record["time"] = time
      record["file"] = tag

      filesplit = tag.split(".")
      record["user"] = filesplit[2]
      record["jid"] = filesplit[3]
      record["tid"] = filesplit[4]

      record
    end
  end
end
