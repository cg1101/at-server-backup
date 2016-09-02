<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="root">
<span><xsl:apply-templates /></span>
</xsl:template>

<xsl:template match="tag">
<xsl:param name="tagtype"><xsl:value-of select="@tagtype" /></xsl:param>
<xsl:choose>

<xsl:when test="$tagtype = 'standalone'">
<xsl:text> </xsl:text>
<xsl:element name="img">
 <xsl:attribute name="tagid"><xsl:value-of select="@tagid" /></xsl:attribute>
 <xsl:attribute name="tagtype"><xsl:value-of select="@tagtype" /></xsl:attribute>
 <xsl:attribute name="src">
  <xsl:value-of select="@tagimg" />
 </xsl:attribute>
</xsl:element>
<xsl:text> </xsl:text>
</xsl:when>

<xsl:when test="$tagtype = 'markup'">
<span>
 <xsl:attribute name="tagid"><xsl:value-of select="@tagid" /></xsl:attribute>
 <xsl:attribute name="tagtype"><xsl:value-of select="@tagtype" /></xsl:attribute>
 <xsl:attribute name="style">
  <xsl:value-of select="@tagstyle" />
 </xsl:attribute>
 <xsl:value-of select="." />
</span>
</xsl:when>

<xsl:when test="$tagtype = 'subst'">
<span>
<xsl:attribute name="tagid"><xsl:value-of select="@tagid" /></xsl:attribute>
<xsl:attribute name="toword"><xsl:value-of select="@toword"/></xsl:attribute>
<xsl:attribute name="fromword"><xsl:value-of select="@fromword"/></xsl:attribute>
<xsl:attribute name="title"><xsl:value-of select="@fromword"/></xsl:attribute>
<xsl:attribute name="class"><xsl:value-of select="$tagtype"/></xsl:attribute>
<xsl:value-of select="text()"/>
<span class="deleteme">(<xsl:value-of select="@fromword"/>)</span>
</span>
</xsl:when>

<xsl:when test="$tagtype = 'Entity'">
<span>

</span>
</xsl:when>

<xsl:otherwise>
<xsl:message terminate="yes">
Error: unknown tag type '<xsl:value-of select="$tagtype"/>'
</xsl:message>
</xsl:otherwise>

</xsl:choose>

</xsl:template>

</xsl:stylesheet>

