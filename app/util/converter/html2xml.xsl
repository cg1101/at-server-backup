<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<!-- source tree is html document to be parsed-->

<!-- process body only, ignore head -->
<xsl:template match="body">
<root><xsl:apply-templates /></root>
</xsl:template>

<!-- img element with tagid attribute are event tags -->
<xsl:template match="img[@tagid and not(@timestamp-value)]">
<xsl:element name="tag">
<xsl:attribute name="tagid"><xsl:value-of select="@tagid" /></xsl:attribute>
<xsl:attribute name="tagtype">Event</xsl:attribute>
</xsl:element>
</xsl:template>

<!-- time stamps -->
<xsl:template match="img[@tagid and @timestamp-value]">
<xsl:element name="timestamp">
<xsl:attribute name="tagid"><xsl:value-of select="@tagid" /></xsl:attribute>
<xsl:attribute name="tagtype">Timestamped</xsl:attribute>
<xsl:attribute name="value"><xsl:value-of select="@timestamp-value" /></xsl:attribute>
</xsl:element>
</xsl:template>

<!-- span.deleteme was used for DEFT tasks, they should be deleted in xml format -->
<xsl:template match="span[contains(@class, 'deleteme')]">
<!--
<xsl:message terminate="no">found span.deleteme</xsl:message>
-->
</xsl:template>

<!-- span element with tagid should be converted to various kinds of tags -->
<xsl:template match="span[@tagid]">

<!-- always create tag element -->
<xsl:element name="tag">

<!-- tagid must always be present -->
<xsl:attribute name="tagid"><xsl:value-of select="@tagid" /></xsl:attribute>

<!-- tagtype must also be present, add this for subst tags -->
<xsl:attribute name="tagtype">
<xsl:choose>
<xsl:when test="contains(@class, 'subst')">subst</xsl:when>
<xsl:otherwise><xsl:value-of select="@tagtype" /></xsl:otherwise>
</xsl:choose>
</xsl:attribute>

<!-- copy all remaining attributes, ignoring all known ones that belong to html -->
<xsl:for-each select="@*" >
<xsl:variable name="attr" select="local-name()" />
<xsl:choose>
<!-- skip known html attributes -->
<xsl:when test="$attr = 'id' or $attr = 'style' or $attr = 'class' or $attr = 'title'"></xsl:when>
<xsl:when test="$attr = 'dir' or $attr = 'lang'"></xsl:when>
<xsl:when test="starts-with($attr, 'onkey') or starts-with($attr, 'onmouse') or $attr = 'onclick' or $attr = 'ondblclick'"></xsl:when>
<!-- and copy the rest in case they are needed -->
<xsl:otherwise><xsl:copy/></xsl:otherwise>
</xsl:choose>
</xsl:for-each>

<xsl:apply-templates />
</xsl:element>
</xsl:template>

<!-- purge other unwanted elemenets -->
<xsl:template match="head"></xsl:template>
<!-- %head.content; "TITLE & BASE?" -->
<xsl:template match="title"></xsl:template>
<xsl:template match="base"></xsl:template>
<!-- %head.misc; "SCRIPT|STYLE|META|LINK|OBJECT" -->
<xsl:template match="script"></xsl:template>
<xsl:template match="style"></xsl:template>
<xsl:template match="meta"></xsl:template>
<xsl:template match="link"></xsl:template>
<xsl:template match="object"></xsl:template>


<!-- some block level stuff should be removed, but not all -->
<!-- %block; "P | %heading; | %list; | %preformatted; | DL | DIV | NOSCRIPT |
      BLOCKQUOTE | FORM | HR | TABLE | FIELDSET | ADDRESS" -->

<xsl:template match="noscript"></xsl:template>
<xsl:template match="applet"></xsl:template>

<!-- tables might be added so parse them now
<xsl:template match="table"></xsl:template>
<xsl:template match="caption"></xsl:template>
<xsl:template match="col"></xsl:template>
<xsl:template match="colgroup"></xsl:template>
<xsl:template match="thead"></xsl:template>
<xsl:template match="tfoot"></xsl:template>
<xsl:template match="tbody"></xsl:template>
<xsl:template match="tr"></xsl:template>
<xsl:template match="th"></xsl:template>
<xsl:template match="td"></xsl:template>
-->

<!-- form related -->
<xsl:template match="form"></xsl:template>
<xsl:template match="input"></xsl:template>
<xsl:template match="button"></xsl:template>
<xsl:template match="select"></xsl:template>
<xsl:template match="option"></xsl:template>
<xsl:template match="optgroup"></xsl:template>
<xsl:template match="textarea"></xsl:template>
<xsl:template match="isindex"></xsl:template>
<xsl:template match="label"></xsl:template>
<xsl:template match="fieldset"></xsl:template>
<xsl:template match="legend"></xsl:template>


<!-- elements from Frameset.dtd -->
<xsl:template match="frame"></xsl:template>
<xsl:template match="frameset"></xsl:template>
<xsl:template match="noframes"></xsl:template>

<xsl:template match="iframe"></xsl:template>

<!-- br tags should be kept -->
<xsl:template match="br">
<br/>
</xsl:template>

<!-- add br at the end of div -->
<xsl:template match="div">
<br/>
<xsl:apply-templates/>
<br/>
</xsl:template>

</xsl:stylesheet>

