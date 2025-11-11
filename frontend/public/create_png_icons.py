#!/usr/bin/env python3
"""
Script para crear iconos PNG desde SVG.
Requiere: pip install cairosvg pillow
O usa: pip install pillow (y convierte SVG a PNG manualmente)
"""

import os
import sys

def create_png_with_pillow(size, output_path):
    """Crear un PNG básico usando Pillow"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Crear imagen
        img = Image.new('RGB', (size, size), color='#3b82f6')
        draw = ImageDraw.Draw(img)
        
        # Dibujar círculo
        margin = 30
        draw.ellipse([margin, margin, size-margin, size-margin], fill='#1e40af')
        
        # Dibujar texto "P2P"
        try:
            # Intentar usar una fuente del sistema
            font_size = size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Si no hay fuente, usar fuente por defecto
            font = ImageFont.load_default()
        
        text = "P2P"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2 - 10
        
        draw.text((text_x, text_y), text, fill='white', font=font)
        
        # Guardar
        img.save(output_path, 'PNG')
        print(f"✓ {output_path} creado exitosamente ({size}x{size})")
        return True
        
    except ImportError:
        print("⚠ Pillow no está instalado. Instala con: pip install pillow")
        return False
    except Exception as e:
        print(f"❌ Error creando {output_path}: {e}")
        return False

def create_png_with_cairo(size, output_path, svg_path):
    """Crear PNG desde SVG usando CairoSVG"""
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=output_path, output_width=size, output_height=size)
        print(f"✓ {output_path} creado desde SVG ({size}x{size})")
        return True
    except ImportError:
        print("⚠ CairoSVG no está instalado. Instala con: pip install cairosvg")
        return False
    except Exception as e:
        print(f"❌ Error creando {output_path}: {e}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Crear icono 192x192
    icon192_path = os.path.join(script_dir, 'icon-192.png')
    icon512_path = os.path.join(script_dir, 'icon-512.png')
    svg192_path = os.path.join(script_dir, 'icon-192.svg')
    svg512_path = os.path.join(script_dir, 'icon-512.svg')
    
    print("Generando iconos PNG...")
    print("=" * 50)
    
    # Intentar crear desde SVG primero
    if os.path.exists(svg192_path):
        if create_png_with_cairo(192, icon192_path, svg192_path):
            pass
        elif create_png_with_pillow(192, icon192_path):
            pass
        else:
            print("❌ No se pudo crear icon-192.png")
            print("   Instala Pillow: pip install pillow")
            print("   O usa el archivo generate-png-from-svg.html en tu navegador")
    else:
        print("⚠ icon-192.svg no encontrado")
    
    if os.path.exists(svg512_path):
        if create_png_with_cairo(512, icon512_path, svg512_path):
            pass
        elif create_png_with_pillow(512, icon512_path):
            pass
        else:
            print("❌ No se pudo crear icon-512.png")
            print("   Instala Pillow: pip install pillow")
            print("   O usa el archivo generate-png-from-svg.html en tu navegador")
    else:
        print("⚠ icon-512.svg no encontrado")
    
    print("=" * 50)
    print("✅ Proceso completado")
    print("\nSi los iconos no se crearon, usa una de estas opciones:")
    print("1. Abre generate-png-from-svg.html en tu navegador")
    print("2. Instala Pillow: pip install pillow")
    print("3. Usa una herramienta online: https://cloudconvert.com/svg-to-png")

if __name__ == '__main__':
    main()

