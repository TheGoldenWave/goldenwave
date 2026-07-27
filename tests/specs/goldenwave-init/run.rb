#!/usr/bin/env ruby
# frozen_string_literal: true

Dir[File.join(__dir__, "*.spec.rb")].sort.each do |file|
  require File.expand_path(file)
end
