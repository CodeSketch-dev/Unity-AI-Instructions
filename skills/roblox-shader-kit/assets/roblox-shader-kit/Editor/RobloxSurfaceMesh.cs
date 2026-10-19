using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace RobloxShaderKit.Editor
{
    // Source contract: Map_BatchBaker / Problox_Batched_Surface. No scene dependencies.
    public sealed class RobloxSurfaceMesh
    {
        readonly List<Vector3> _positions = new();
        readonly List<Vector3> _normals = new();
        readonly List<Vector2> _uv = new();
        readonly List<Vector4> _surface = new(), _movement = new();
        readonly List<Color> _colors = new();
        readonly List<int> _indices = new();
        public int VertexCount => _positions.Count;

        public void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Color color,
            int flags = 3, int slot = 0, float tiling = 1, Vector2 movement = default)
        {
            if ((flags & 6) != 0 && (flags & 1) == 0)
                throw new ArgumentException("Stud/checker requires the texture bit.");
            int start = _positions.Count;
            var normal = Vector3.Cross(b - a, c - a).normalized;
            if (normal.sqrMagnitude < .9f) throw new ArgumentException("Degenerate face");
            float width = Vector3.Distance(a, b) * tiling, height = Vector3.Distance(b, c) * tiling;
            var linear = color.linear; linear.a = 1;
            Vector3[] points = { a, b, c, d };
            Vector2[] uv = { Vector2.zero, new(width, 0), new(width, height), new(0, height) };
            for (int i = 0; i < 4; i++)
            {
                _positions.Add(points[i]); _normals.Add(normal); _colors.Add(linear); _uv.Add(uv[i]);
                _surface.Add(new Vector4(flags, slot, 4, 2));
                _movement.Add(new Vector4(movement.x, movement.y, 0, 0));
            }
            _indices.AddRange(new[] { start, start + 1, start + 2, start, start + 2, start + 3 });
        }

        // Bottom-centre pivot; faces have separate vertices, flat normals and metric UVs.
        public void Box(Vector3 bottom, Vector3 size, Color color, Quaternion rotation = default,
            int flags = 3, int slot = 0, float tiling = 1)
        {
            if (size.x <= 0 || size.y <= 0 || size.z <= 0) throw new ArgumentException("Positive size required");
            if (rotation == default) rotation = Quaternion.identity;
            var half = size * .5f; var centre = bottom + Vector3.up * half.y;
            Vector3 P(float x, float y, float z) => centre + rotation * Vector3.Scale(new Vector3(x,y,z), half);
            Quad(P(-1,-1,-1),P(-1,1,-1),P(1,1,-1),P(1,-1,-1),color,flags,slot,tiling);
            Quad(P(1,-1,1),P(1,1,1),P(-1,1,1),P(-1,-1,1),color,flags,slot,tiling);
            Quad(P(-1,-1,1),P(-1,1,1),P(-1,1,-1),P(-1,-1,-1),color,flags,slot,tiling);
            Quad(P(1,-1,-1),P(1,1,-1),P(1,1,1),P(1,-1,1),color,flags,slot,tiling);
            Quad(P(-1,1,-1),P(-1,1,1),P(1,1,1),P(1,1,-1),color,flags,slot,tiling);
            Quad(P(-1,-1,1),P(-1,-1,-1),P(1,-1,-1),P(1,-1,1),color,flags,slot,tiling);
        }

        public void Beam(Vector3 a, Vector3 b, float width, Color color)
        {
            var centre = (a + b) * .5f;
            Box(centre - Vector3.up * Vector3.Distance(a,b) * .5f,
                new Vector3(width,Vector3.Distance(a,b),width),color,Quaternion.FromToRotation(Vector3.up,b-a));
        }

        public void Ellipsoid(Vector3 centre, Vector3 radii, Color color, int segments = 12, int rings = 8, int flags = 0)
        {
            if(segments<3 || rings<2 || radii.x<=0 || radii.y<=0 || radii.z<=0) throw new ArgumentException("Invalid ellipsoid");
            Vector3 P(int row,int column) {
                float lat=-Mathf.PI/2+Mathf.PI*row/rings, lon=Mathf.PI*2*column/segments;
                return centre+Vector3.Scale(radii,new Vector3(Mathf.Cos(lat)*Mathf.Cos(lon),Mathf.Sin(lat),Mathf.Cos(lat)*Mathf.Sin(lon)));
            }
            // Winding follows latitude then longitude for outward-facing normals.
            for(int row=1;row<rings-1;row++)for(int col=0;col<segments;col++)
                Quad(P(row,col),P(row+1,col),P(row+1,col+1),P(row,col+1),color,flags);
            for(int col=0;col<segments;col++) {
                Triangle(centre-Vector3.up*radii.y,P(1,col),P(1,col+1),color,flags);
                Triangle(P(rings-1,col),centre+Vector3.up*radii.y,P(rings-1,col+1),color,flags);
            }
        }

        void Triangle(Vector3 a,Vector3 b,Vector3 c,Color color,int flags)
        {
            int start=_positions.Count; var normal=Vector3.Cross(b-a,c-a).normalized;
            var linear=color.linear; linear.a=1;
            Vector3[] points={a,b,c};
            Vector2[] uvs={Vector2.zero,new Vector2(Vector3.Distance(a,b),0),new Vector2(0,Vector3.Distance(a,c))};
            for(int i=0;i<3;i++) {
                _positions.Add(points[i]);_normals.Add(normal);_colors.Add(linear);_uv.Add(uvs[i]);
                _surface.Add(new Vector4(flags,0,4,2));_movement.Add(Vector4.zero);
            }
            _indices.Add(start);_indices.Add(start+1);_indices.Add(start+2);
        }

        public Mesh Build(string name)
        {
            if (_positions.Count == 0 || _positions.Count > 2000000) throw new InvalidOperationException("Mesh budget");
            var mesh = new Mesh { name = name, indexFormat = _positions.Count > 65535 ? IndexFormat.UInt32 : IndexFormat.UInt16 };
            mesh.SetVertices(_positions); mesh.SetNormals(_normals); mesh.SetColors(_colors);
            mesh.SetUVs(0,_uv); mesh.SetUVs(1,_surface); mesh.SetUVs(2,_movement);
            mesh.SetTriangles(_indices,0); mesh.RecalculateTangents(); mesh.RecalculateBounds();
            Validate(mesh); return mesh;
        }

        public static void Validate(Mesh mesh)
        {
            var surface = new List<Vector4>(); var movement = new List<Vector4>();
            mesh.GetUVs(1,surface); mesh.GetUVs(2,movement);
            if (mesh.colors.Length != mesh.vertexCount || mesh.uv.Length != mesh.vertexCount ||
                surface.Count != mesh.vertexCount || movement.Count != mesh.vertexCount || mesh.tangents.Length != mesh.vertexCount)
                throw new InvalidOperationException("Incomplete batched vertex contract");
            foreach (var data in surface)
            {
                int flags = Mathf.RoundToInt(data.x);
                if (((flags & 6) != 0 && (flags & 1) == 0) || data.z < 1 || data.y < 0 || data.y > 4)
                    throw new InvalidOperationException("Invalid surface flags/slot/checker tiling");
            }
            foreach (int index in mesh.triangles)
                if (index < 0 || index >= mesh.vertexCount) throw new InvalidOperationException("Invalid index");
        }
    }
}
