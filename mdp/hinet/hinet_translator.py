"""
Module to translate HiNet structures into other representations, like HTML.
"""

import mdp

import switchboard


class HiNetTranslator(object):
    """Generic translation class for HiNet flow.
    
    The dummy implementation in this base class turns the HiNet structure
    into nested lists of the basic nodes.
    """
    
    def __init__(self):
        """Initialize the internal variables."""
        pass

    def _translate_flow(self, flow):
        """Translate the flow and return the translation."""
        flow_translation = []
        for node in flow:
            flow_translation.append(self._translate_node(node))
        return flow_translation
            
    def _translate_node(self, node):
        """Translate a node and return the translation.
        
        Depending on the type of the node this can be delegated to more
        specific methods.
        """
        if isinstance(node, mdp.hinet.FlowNode):
            return self._translate_flownode(node)
        if isinstance(node, mdp.hinet.CloneLayer):
            return self._translate_clonelayer(node)
        elif isinstance(node, mdp.hinet.Layer):
            return self._translate_layer(node)
        else:
            return self._translate_standard_node(node)
        
    def _translate_flownode(self, flownode):
        """Translate a flow node and return the translation.
        
        The internal nodes are translated recursively.
        """
        flownode_translation = []
        flow = flownode._flow
        for node in flow.flow:
            flownode_translation.append(self._translate_node(node))
        return flownode_translation
    
    def _translate_layer(self, layer):
        """Translate a layer and return the translation.
        
        All the nodes in the layer are translated.
        """
        layer_translation = []
        for node in layer.nodes:
            layer_translation.append(self._translate_node(node))
        return layer_translation
    
    def _translate_clonelayer(self, clonelayer):
        """Translate a CloneLayer and return the translation."""
        translated_node = self._translate_node(clonelayer.node)
        return [translated_node] * len(clonelayer.nodes)

    def _translate_standard_node(self, node):
        """Translate a node and return the translation.
        
        This method is used when no specialized translation (like for FlowNodes
        or Layers) is required.
        """
        return node


## Specialized HTML Translator ##

# CSS for hinet representation.
#
# Warning: In nested tables the top table css overwrites the nested css if
#    they are specified like 'table.flow td' (i.e. all td's below this table).
#    So be careful about hiding/overriding nested td's.
#
# The tables "nodestruct" are used to separate the dimension values from 
# the actual node text.

HINET_STYLE = """
table.flow {
    border-collapse: separate;
    padding: 3 3 3 3;
    border: 3px double;
    border-color: #003399;
}

table.flow table {
    width: 100%;
    margin-left: 2px;
    margin-right: 2px;
    border-color: #003399; 
}

table.flow td {
    padding: 1 5 1 5;
    border-style: none;
}

table.layer {
    border-collapse: separate;
    border: 2px dashed;
}

table.flownode {
    border-collapse: separate;
    border: 1px dotted;
}

table.nodestruct {
    border-style: none;
}

table.node {
    border-collapse: separate;
    border: 1px solid;
    border-spacing: 2px;
}

td.nodename {
    font-size: normal;
    text-align: center;
}

td.nodeparams {
    font-size: xx-small;
    text-align: left;
}

td.dim {
    font-size: xx-small;
    text-align: center;
    color: #008ADC;
}
"""

# Functions to define how the node parameters are represented in the
# HTML representation of a node.
#
# Note that the list is worked starting from the end (so subclasses can
# be appended to the end of the list to override their parent class writer).
    
def _get_html_rect2dswitchboard(node):
    return ['rec. field size (in channels): %d x %d = %d' % 
                (node.x_field_channels, node.y_field_channels,
                 node.x_field_channels * node.y_field_channels),
            '# of rec. fields (output channels): %d x %d = %d' %
                (node.x_out_channels, node.y_out_channels,
                 node.x_out_channels * node.y_out_channels),
            'rec. field distances (in channels): (%d, %d)' %
                (node.x_field_spacing, node.y_field_spacing),
            'channel width: %d' % node.in_channel_dim]
    
def _get_html_sfa2(node):
    return ['expansion dim: ' + str(node._expnode.output_dim)]
    
def _get_html_normalnoise(node):
    return ['noise level: ' + str(node.noise_args[1]),
            'noise offset: ' + str(node.noise_args[0])]
    
# (node class type, write function)
NODE_HTML_TRANSLATORS = [
    (switchboard.Rectangular2dSwitchboard, _get_html_rect2dswitchboard),
    (mdp.nodes.SFA2Node, _get_html_sfa2),
    (mdp.nodes.NormalNoiseNode, _get_html_normalnoise),
]


class NewlineWriteFile(object):
    """Decorator for file-like object.
    
    Adds a newline character to each line written with write().
    """
    
    def __init__(self, file_obj):
        """Wrap the given file-like object."""
        self.file_obj = file_obj
    
    def write(self, str_obj):
        """Write a string to the file object and append a newline character."""
        self.file_obj.write(str_obj + "\n")
        
    def close(self):
        self.file_obj.close()
    
    
class HiNetHTMLTranslator(HiNetTranslator):
    """Specialized translator for HTML.
    
    Instead of relying on the return values the HTML lines are directly
    written to a provided file.
    """
    
    def __init__(self, node_param_translators=NODE_HTML_TRANSLATORS):
        """Initialize the HMTL translator.
        
        node_param_translators -- List of tuples, the first tuple entry beeing
            the node type and the second a functions that translates the the
            internal node parameters into HTML. The function returns a list
            of HTML lines, which are then written into the HTML file.
            Note that the list is worked starting from the end (so subclasses 
            can be appended to the end of the list to override their parent 
            class).
        """
        self._node_param_translators = node_param_translators
        self._html_file = None
        
    def write_flow_to_file(self, flow, html_file):
        """Write the HTML translation of the flow into the provided file."""
        self._html_file = NewlineWriteFile(html_file)
        self._translate_flow(flow)
        self._html_file = None
    
    def add_node_param_translators(self, node_param_translators):
        """Append more node_param_translators (see __init__)."""
        self._node_param_translators += node_param_translators  
        
    # overwrite methods
    
    def _translate_flow(self, flow):
        """Translate the flow into HTML and write it into the internal file.
        
        Use write_flow_to_file instead of calling this method.
        """
        f = self._html_file
        self._open_node_env(flow, "flow")
        for node in flow:
            f.write('<tr><td>')
            self._translate_node(node)
            f.write('</td></tr>')
        f.write('</td></tr>')
        self._close_node_env(flow, "flow")
        
    def _translate_flownode(self, flownode):
        f = self._html_file
        self._open_node_env(flownode, "flownode")
        flow = flownode._flow
        for node in flow.flow:
            f.write('<tr><td>')
            self._translate_node(node)
            f.write('</td></tr>')
        self._close_node_env(flownode, "flownode")
     
    def _translate_layer(self, layer):
        f = self._html_file
        self._open_node_env(layer, "layer")
        f.write('<tr>')
        for node in layer.nodes:
            f.write('<td>')
            self._translate_node(node)
            f.write('</td>')
        f.write('</tr>')
        self._close_node_env(layer)
        
    def _translate_clonelayer(self, clonelayer):
        f = self._html_file
        self._open_node_env(clonelayer, "layer")
        f.write('<tr><td class="nodename">')
        f.write(str(clonelayer) + '<br><br>')
        f.write('%d repetitions' % len(clonelayer.nodes))
        f.write('</td>')
        f.write('<td>')
        self._translate_node(clonelayer.node)
        f.write('</td></tr>')
        self._close_node_env(clonelayer)

    def _translate_standard_node(self, node):
        f = self._html_file
        self._open_node_env(node)
        f.write('<tr><td class="nodename">')
        f.write(str(node))
        f.write('</td></tr>')
        f.write('<tr><td class="nodeparams">')
        for node_param_trans in self._node_param_translators[::-1]:
            if isinstance(node, node_param_trans[0]):
                html_params = " <br>\n".join(node_param_trans[1](node))
                f.write(html_params)
                break
        f.write('</td></tr>')
        self._close_node_env(node)
        
    # helper methods for decoration
    
    def _open_node_env(self, node, type_id="node"):
        """Open the HTML environment for the node internals.
        
        node -- The node itself.
        type_id -- The id string as used in the CSS.
        """
        f = self._html_file
        f.write('<table class="%s">' % type_id)
        if not (type_id=="flow" or type_id=="flownode"):
            f.write('<tr><td class="dim">in-dim: %d</td></tr>' % node.input_dim)
        f.write('<tr><td>')
        f.write('<table class="nodestruct">')
    
    def _close_node_env(self, node, type_id="node"):
        """Close the HTML environment for the node internals.
        
        node -- The node itself.
        type_id -- The id string as used in the CSS.
        """
        f = self._html_file
        f.write('</table>')
        f.write('</td></tr>')
        if not (type_id=="flow" or type_id=="flownode"):
            f.write('<tr><td class="dim">out-dim: %d' % node.output_dim)
            f.write('</td></tr>')
        f.write('</table>')
    
        
